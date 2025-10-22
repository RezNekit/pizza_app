from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from datetime import date
from decimal import Decimal
from models import db, Customer, Address, BirthdayDiscount
from controllers import mark_delivered
from order_placement import place_order
from constraint_tests import calculate_problems
from reports import *


VAT_RATE = 1.09 #this is our VAT rate


menu_bp = Blueprint("menu", __name__)
customers_bp = Blueprint("customers", __name__)
orders_bp = Blueprint("orders", __name__)

@menu_bp.route("/pizzas")
def list_pizzas():
    sql = text("""
        SELECT p.pizza_id, p.name, p.is_vegetarian, p.is_vegan, p.is_spicy,   -- add is_spicy
           pr.price_ex_vat, pr.price_inc_vat
        FROM Pizza AS p
        JOIN v_pizza_price AS pr ON pr.pizza_id = p.pizza_id
        ORDER BY p.pizza_id
    """)
    rows = db.session.execute(sql).mappings().all()
    return render_template("pizzas.html", title="Pizzas", pizzas=rows)

@menu_bp.route("/drinks")
def list_drinks():
    rows = db.session.execute(text("""
        SELECT drink_id, name, size_ml, price_ex_vat, price_inc_vat
        FROM v_drink_price
        ORDER BY drink_id
    """)).mappings().all()
    return render_template("drinks.html", title="Drinks", drinks=rows)

@menu_bp.route("/desserts")
def list_desserts():
    rows = db.session.execute(text("""
        SELECT dessert_id, name, price_ex_vat, price_inc_vat
        FROM v_dessert_price
        ORDER BY dessert_id
    """)).mappings().all()
    return render_template("desserts.html", title="Desserts", desserts=rows)

@customers_bp.route("/customers")
def list_customers():
    customers = Customer.query.order_by(Customer.customer_id).all()
    return render_template("customers.html", title="Customers", customers=customers)

@customers_bp.get("/customers/new", endpoint="new_customer")
def new_customer():
    # Render the form for creating a customer
    return render_template("customer_form.html", title="New customer")

@customers_bp.post("/customers", endpoint="create_customer_post")
def create_customer_post():
    # Required fields
    first_name = (request.form.get("first_name") or "").strip()
    last_name  = (request.form.get("last_name") or "").strip()
    email      = (request.form.get("email") or "").strip()
    phone      = (request.form.get("phone") or "").strip()

    # Optional fields (but validated if present)
    gender_raw = (request.form.get("gender") or "").strip()
    gender = gender_raw[:1].upper() if gender_raw else None

    birth_date_str = (request.form.get("birth_date") or "").strip()
    birth_dt = None
    if birth_date_str:
        try:
            birth_dt = date.fromisoformat(birth_date_str)  # YYYY-MM-DD
        except ValueError:
            flash("Birth date must be YYYY-MM-DD.", "error")
            return redirect(url_for("customers.new_customer"))
        if birth_dt > date.today():
            flash("Birth date cannot be in the future.", "error")
            return redirect(url_for("customers.new_customer"))

    # Address (required – per your models and earlier request)
    street      = (request.form.get("street") or "").strip()
    city        = (request.form.get("city") or "").strip()
    postal_code = (request.form.get("postal_code") or "").strip()
    country     = (request.form.get("country") or "").strip()

    if not all([first_name, last_name, email, phone, street, city, postal_code, country]):
        flash("First name, last name, email, phone and full address are required.", "error")
        return redirect(url_for("customers.new_customer"))

    # Uniqueness checks (NO regex, NO hashing — just simple queries)
    existing = Customer.query.filter(
        (Customer.email == email) | (Customer.phone == phone)
    ).one_or_none()
    if existing:
        flash("A customer with this email or phone already exists.", "error")
        return redirect(url_for("customers.new_customer"))

    # Reuse or create the Address row
    addr = Address.query.filter_by(
        street=street, city=city, postal_code=postal_code, country=country
    ).one_or_none()
    if not addr:
        addr = Address(street=street, city=city, postal_code=postal_code, country=country)
        db.session.add(addr)
        db.session.flush()  # get address_id

    # Create the Customer respecting models.py constraints
    c = Customer(
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_dt,
        email=email,
        phone=phone,
        gender=gender,
        address_id=addr.address_id
    )
    db.session.add(c)
    db.session.commit()

    flash("Customer created.", "success")
    return redirect(url_for("customers.list_customers"))


def _birthday_freebie_consume(customer: Customer, item_kind: str) -> bool:
    """
    Try to consume a birthday freebie for this customer and item kind ("pizza" or "drink").
    Returns True iff a freebie was applied and consumed.
    """
    if not customer or not customer.birth_date:
        return False

    today = date.today()
    if (customer.birth_date.month, customer.birth_date.day) != (today.month, today.day):
        return False

    bd = (BirthdayDiscount.query
          .filter_by(customer_id=customer.customer_id, year=today.year)
          .one_or_none())
    if bd is None:
        bd = BirthdayDiscount(customer_id=customer.customer_id, year=today.year)
        db.session.add(bd)
        db.session.flush()

    if item_kind == "drink" and bd.freedrink_available:
        bd.freedrink_available = False
        return True
    if item_kind == "pizza" and bd.freepizza_available:
        bd.freepizza_available = False
        return True

    return False

@orders_bp.route("/orders")
def list_orders():

    # Get basic order info
    sql = text("""
        SELECT
            o.order_id,
            o.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
            o.order_date,
            o.current_status,
            CASE
                WHEN dp.first_name IS NULL THEN '—'
                ELSE CONCAT(dp.first_name, ' ', dp.last_name)
            END AS driver_name
        FROM Orders o
        LEFT JOIN Customers c ON c.customer_id = o.customer_id
        LEFT JOIN Delivery_Person dp ON dp.delivery_person_id = o.delivery_person_id
        WHERE o.cancelled_at IS NULL
        GROUP BY o.order_id, o.customer_id, c.first_name, c.last_name, dp.first_name, dp.last_name,
                 o.order_date, o.current_status
        ORDER BY o.order_id DESC
    """)
    orders = db.session.execute(sql).mappings().all()
    
    enriched_orders = []
    
    for order_row in orders:
        order_id = order_row['order_id']
        customer_id = order_row['customer_id']
        
        # Get order items
        items_sql = text("""
            SELECT 
                oi.order_item_id,
                oi.quantity,
                oi.price_excl_vat,
                CASE 
                    WHEN oi.pizza_id IS NOT NULL THEN p.name
                    WHEN oi.drink_id IS NOT NULL THEN d.name || ' (' || d.size_ml || 'ml)'
                    WHEN oi.dessert_id IS NOT NULL THEN ds.name
                END AS name,
                CASE 
                    WHEN oi.pizza_id IS NOT NULL THEN 'Pizza'
                    WHEN oi.drink_id IS NOT NULL THEN 'Drink'
                    WHEN oi.dessert_id IS NOT NULL THEN 'Dessert'
                END AS type
            FROM OrderItem oi
            LEFT JOIN Pizza p ON p.pizza_id = oi.pizza_id
            LEFT JOIN Drink d ON d.drink_id = oi.drink_id
            LEFT JOIN Dessert ds ON ds.dessert_id = oi.dessert_id
            WHERE oi.order_id = :oid
            ORDER BY oi.order_item_id
        """)
        order_items = [dict(row) for row in db.session.execute(items_sql, {"oid": order_id}).mappings().all()]
        
        # Calculate subtotal
        subtotal_sql = text("""
            SELECT COALESCE(SUM(price_excl_vat * quantity), 0) as subtotal
            FROM OrderItem
            WHERE order_id = :oid
        """)
        subtotal = float(db.session.execute(subtotal_sql, {"oid": order_id}).scalar() or 0)
        
        # Calculate birthday discount
        birthday_sql = text("""
            SELECT COALESCE(SUM(
                CASE 
                    WHEN price_excl_vat = 0 AND quantity = 1 
                    THEN (SELECT price_ex_vat FROM v_pizza_price WHERE pizza_id = oi.pizza_id)
                    WHEN price_excl_vat = 0 AND quantity = 1 AND oi.drink_id IS NOT NULL
                    THEN (SELECT price_ex_vat FROM v_drink_price WHERE drink_id = oi.drink_id)
                    ELSE 0
                END
            ), 0) as birthday_discount
            FROM OrderItem oi
            WHERE order_id = :oid
        """)
        birthday_discount = float(db.session.execute(birthday_sql, {"oid": order_id}).scalar() or 0)
        
        # Calculate loyalty discount
        loyalty_discount = 0.0
        loyalty_milestones = 0
        if customer_id:
            pizzas_before_sql = text("""
                SELECT COALESCE(SUM(oi.quantity), 0)
                FROM OrderItem oi
                JOIN Orders o ON o.order_id = oi.order_id
                WHERE o.customer_id = :cid
                  AND oi.pizza_id IS NOT NULL
                  AND o.cancelled_at IS NULL
                  AND o.order_id < :oid
            """)
            pizzas_before = int(db.session.execute(pizzas_before_sql, 
                {"cid": customer_id, "oid": order_id}).scalar() or 0)
            
            pizzas_in_order_sql = text("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM OrderItem
                WHERE order_id = :oid AND pizza_id IS NOT NULL
            """)
            pizzas_in_order = int(db.session.execute(pizzas_in_order_sql, 
                {"oid": order_id}).scalar() or 0)
            
            if pizzas_in_order > 0:
                before_milestone = pizzas_before // 10
                after_milestone = (pizzas_before + pizzas_in_order) // 10
                loyalty_milestones = max(0, after_milestone - before_milestone)
                
                if loyalty_milestones > 0:
                    loyalty_discount = round(subtotal * 0.30 * loyalty_milestones, 2)
        
        # Calculate code discount
        code_discount = 0.0
        code_name = None
        discount_record = db.session.execute(text("""
            SELECT d.discount_code_id
            FROM Discount d
            WHERE d.order_id = :oid
            LIMIT 1
        """), {"oid": order_id}).first()
        
        if discount_record:
            dc_id = discount_record[0]
            discount_code = db.session.execute(text("""
                SELECT code, percentage_off
                FROM DiscountCode
                WHERE discount_code_id = :dcid
            """), {"dcid": dc_id}).first()
            
            if discount_code:
                code_name = discount_code[0]
                if discount_code[1]:
                    percentage = float(discount_code[1])
                    code_discount = round(subtotal * percentage / 100.0, 2)

        total_discount = round(birthday_discount + loyalty_discount + code_discount, 2)
        total_ex_vat = round(subtotal - loyalty_discount - code_discount, 2)
        total_inc_vat = round(total_ex_vat * VAT_RATE, 2)
        vat_amount = round(total_inc_vat - total_ex_vat, 2)
        
        enriched_orders.append({
            'order_id': order_row['order_id'],
            'customer_name': order_row['customer_name'],
            'order_date': order_row['order_date'],
            'current_status': order_row['current_status'],
            'driver_name': order_row['driver_name'],
            'subtotal_ex_vat': subtotal,
            'discount_ex_vat': total_discount,
            'total_ex_vat': total_ex_vat,
            'total_inc_vat': total_inc_vat,
            'vat_amount': vat_amount,
            'order_items': order_items,
            'discount_details': {
                'birthday_discount': birthday_discount,
                'loyalty_discount': loyalty_discount,
                'loyalty_milestones': loyalty_milestones,
                'code_discount': code_discount,
                'code_name': code_name
            }
        })
    
    return render_template("orders.html", title="Orders", order_rows=enriched_orders)
@orders_bp.route("/orders/new")
def new_order():
    customers = Customer.query.order_by(Customer.first_name, Customer.last_name).all()

    pizzas = db.session.execute(text("""
        SELECT p.pizza_id, p.name, vp.price_ex_vat
        FROM Pizza p
        JOIN v_pizza_price vp ON vp.pizza_id = p.pizza_id
        ORDER BY p.pizza_id
    """)).mappings().all()

    drinks = db.session.execute(text("""
        SELECT d.drink_id, d.name, d.size_ml, vd.price_ex_vat
        FROM Drink d
        JOIN v_drink_price vd ON vd.drink_id = d.drink_id
        ORDER BY d.drink_id
    """)).mappings().all()

    desserts = db.session.execute(text("""
        SELECT ds.dessert_id, ds.name, vds.price_ex_vat
        FROM Dessert ds
        JOIN v_dessert_price vds ON vds.dessert_id = ds.dessert_id
        ORDER BY ds.dessert_id
    """)).mappings().all()

    return render_template(
        "order_form.html",  # or "order_form.html" if you use that filename
        title="New Order",
        customers=customers,
        pizzas=pizzas,
        drinks=drinks,
        desserts=desserts
    )



@orders_bp.route("/orders/create", methods=["POST"])
def create_order():
    # Customer
    try:
        customer_id = int((request.form.get("customer_id") or "").strip())
    except ValueError:
        flash("Please choose a customer.", "error")
        return redirect(url_for("orders.new_order"))

    if not Customer.query.get(customer_id):
        flash("Customer not found.", "error")
        return redirect(url_for("orders.new_order"))

    code = (request.form.get("discount_code") or "").strip() or None

    # Build items from qty_* fields
    items = []
    # pizzas
    for pid, in db.session.execute(text("SELECT pizza_id FROM Pizza ORDER BY pizza_id")).all():
        q = (request.form.get(f"qty_pizza_{pid}") or "0").strip()
        try: q = int(q)
        except ValueError: q = 0
        if q > 0: items.append({"type": "pizza", "id": pid, "qty": q})

    # drinks
    for did, in db.session.execute(text("SELECT drink_id FROM Drink ORDER BY drink_id")).all():
        q = (request.form.get(f"qty_drink_{did}") or "0").strip()
        try: q = int(q)
        except ValueError: q = 0
        if q > 0: items.append({"type": "drink", "id": did, "qty": q})

    # desserts
    for dsid, in db.session.execute(text("SELECT dessert_id FROM Dessert ORDER BY dessert_id")).all():
        q = (request.form.get(f"qty_dessert_{dsid}") or "0").strip()
        try: q = int(q)
        except ValueError: q = 0
        if q > 0: items.append({"type": "dessert", "id": dsid, "qty": q})

    if not any(i for i in items if i["type"] == "pizza"):
        flash("Please choose at least one pizza.", "error")
        return redirect(url_for("orders.new_order"))

    # Create the order (summary is guaranteed)
    try:
        summary = place_order(customer_id, items, discount_code=code)
    except Exception as e:
    
        flash("Could not create order: " + str(e), "error")
        return redirect(url_for("orders.new_order"))

    
    if code:
        if not summary.get("code_applied"):
            reason = summary.get("code_reason") or "invalid"
            msg = {
                "invalid":      f"Discount code '{code.upper()}' is not valid.",
                "expired":      f"Discount code '{code.upper()}' has expired.",
                "not_started":  f"Discount code '{code.upper()}' is not active yet.",
                "exhausted":    f"Discount code '{code.upper()}' has reached its usage limit.",
                "zero_value":   f"Discount code '{code.upper()}' gives no discount for this order.",
                "already_used": f"You have already used discount code '{code.upper()}'.",
            }.get(reason, f"Discount code '{code.upper()}' cannot be applied.")
            flash(msg, "error")
        else:
            flash(f"Discount code applied: -€{summary.get('code_amount', 0.0):.2f}", "success")

    flash(
        f"Order #{summary['order_id']} created. "
        f"Subtotal €{summary['subtotal_ex_vat']:.2f}, "
        f"discounts €{summary['discounts_ex_vat']:.2f}.",
        "success",
    )
    return redirect(url_for("orders.list_orders"))


@orders_bp.route("/orders/undelivered")
def undelivered_orders():
    rows = db.session.execute(text("""
        SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer_name,
               o.order_date, o.current_status
        FROM Orders o
        LEFT JOIN Customers c ON c.customer_id = o.customer_id
        WHERE o.delivered_at IS NULL AND o.cancelled_at IS NULL
        ORDER BY o.order_date DESC
    """)).mappings().all()
    # render template name you have for undelivered orders
    return render_template("undelivered.html", orders=rows)


@orders_bp.route("/orders/<int:order_id>/delivered", methods=["POST"])
def set_delivered(order_id):
    try:
        mark_delivered(order_id)
    except Exception as e:
        flash(str(e), "error")
    else:
        flash(f"Order #{order_id} marked as delivered.", "success")
    return redirect(url_for("orders.undelivered_orders"))








































@orders_bp.route("/reports")
def reports_dashboard():
    return render_template("reports_dashboard.html", title="Reports Dashboard")


@orders_bp.route("/reports/top-pizzas")
def report_top_pizzas():
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    top_pizzas = get_top_selling_pizzas(limit=limit, days=days)
    
    return render_template(
        "report_top_pizzas.html",
        title="Top Selling Pizzas",
        pizzas=top_pizzas,
        days=days,
        limit=limit
    )

@orders_bp.route("/reports/undelivered-detailed")
def report_undelivered_detailed():
    orders = get_undelivered_orders()
    
    return render_template(
        "report_undelivered.html",
        title="Undelivered Orders Details",
        orders=orders
    )

@orders_bp.route("/reports/earnings-by-gender")
def report_earnings_gender():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    earnings = get_monthly_earnings_by_gender(month=month, year=year)
    
    return render_template(
        "report_earnings_gender.html",
        title="Earnings by Gender",
        earnings=earnings,
        month=month,
        year=year
    )

@orders_bp.route("/reports/earnings-by-age")
def report_earnings_age():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    earnings = get_monthly_earnings_by_age(month=month, year=year)
    
    return render_template(
        "report_earnings_age.html",
        title="Earnings by Age Group",
        earnings=earnings,
        month=month,
        year=year
    )

@orders_bp.route("/reports/earnings-by-postal")
def report_earnings_postal():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    earnings = get_monthly_earnings_by_postal_code(month=month, year=year, limit=limit)
    
    return render_template(
        "report_earnings_postal.html",
        title="Earnings by Postal Code",
        earnings=earnings,
        month=month,
        year=year,
        limit=limit
    )

@orders_bp.route("/reports/constraint-tests")
def report_constraint_tests():
    test_results = calculate_problems()
    return render_template("report_constraints.html", results=test_results)



