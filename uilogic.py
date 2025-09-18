from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from models import db, Pizza, Drink, Dessert, Customer, Order, OrderItem

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

@customers_bp.route("/customers/new")
def new_customer():
    return render_template("customer_form.html", title="New Customer")

@customers_bp.route("/customers", methods=["POST"])
def create_customer():
    first_name = request.form.get("first_name","").strip()
    last_name = request.form.get("last_name","").strip()
    email = request.form.get("email","").strip()
    phone = request.form.get("phone","").strip()
    gender = request.form.get("gender","").strip()[:1].upper() if request.form.get("gender") else None

    if not first_name or not last_name or not email or not phone:
        flash("First name, last name, email and phone are required.", "error")
        return redirect(url_for("customers.new_customer"))

    if Customer.query.filter_by(email=email).first():
        flash("Email already exists.", "error")
        return redirect(url_for("customers.new_customer"))

    c = Customer(first_name=first_name, last_name=last_name, email=email, phone=phone, gender=gender)
    db.session.add(c)
    db.session.commit()
    flash("Customer created.", "success")
    return redirect(url_for("customers.list_customers"))

@orders_bp.route("/orders")
def list_orders():
    orders = (Order.query
              .options(selectinload(Order.customer),
                       selectinload(Order.items))
              .order_by(Order.order_id.desc())
              .all())
    order_rows = []
    for o in orders:
        items = []
        for it in o.items:
            item_name = None
            if it.pizza_id:
                row = db.session.execute(text("SELECT name FROM Pizza WHERE pizza_id = :pid"),
                                         {"pid": it.pizza_id}).first()
                item_name = row[0] if row else "Pizza"
                price_row = db.session.execute(text(
                    "SELECT price_inc_vat FROM v_pizza_price WHERE pizza_id = :pid"),
                    {"pid": it.pizza_id}
                ).first()
                unit_price_inc = float(price_row[0]) if price_row else 0.0
            elif it.dessert_id:
                row = db.session.execute(text("""
                    SELECT name, price_inc_vat FROM v_dessert_price WHERE dessert_id = :did
                """), {"did": it.dessert_id}).first()
                item_name = row[0] if row else "Dessert"
                unit_price_inc = float(row[1]) if row else 0.0

            elif it.drink_id:
                row = db.session.execute(text("""
                    SELECT name, size_ml, price_inc_vat FROM v_drink_price WHERE drink_id = :drid
                """), {"drid": it.drink_id}).first()
                item_name = (f"{row[0]} {row[1]}ml") if row else "Drink"
                unit_price_inc = float(row[2]) if row else 0.0
            else:
                item_name = "Item"
                unit_price_inc = 0.0

            items.append({
                "name": item_name,
                "qty": it.quantity,
                "unit_price_inc": unit_price_inc,
                "line_total_inc": unit_price_inc * it.quantity
            })
        order_rows.append({"order": o, "items": items})

    return render_template("orders.html", title="Orders", order_rows=order_rows)

@orders_bp.route("/orders/new")
def new_order():
    customers = Customer.query.order_by(Customer.first_name, Customer.last_name).all()
    pizzas = db.session.execute(text("""
        SELECT p.pizza_id, p.name, pr.price_ex_vat, pr.price_inc_vat
        FROM Pizza p
        JOIN v_pizza_price pr ON pr.pizza_id = p.pizza_id
        ORDER BY p.name
    """)).mappings().all()
    drinks = Drink.query.order_by(Drink.name).all()
    desserts = Dessert.query.order_by(Dessert.name).all()
    return render_template("order_form.html", title="New Order",
                           customers=customers, pizzas=pizzas,
                           drinks=drinks, desserts=desserts)

@orders_bp.route("/orders", methods=["POST"])
def create_order():
    customer_id = request.form.get("customer_id")
    item_kind = request.form.get("item_kind", "pizza")
    qty = request.form.get("qty", "1")
    try:
        qty = max(1, int(qty))
    except:
        qty = 1

    cust = Customer.query.get(customer_id)
    if not cust:
        flash("Select a valid customer.", "error")
        return redirect(url_for("orders.new_order"))

    # TODO: choose delivery_person_id properly (e.g., by postal code); using 1 as placeholder
    order = Order(customer_id=cust.customer_id, current_status="new", delivery_person_id=1)
    db.session.add(order)
    db.session.flush()

    if item_kind == "pizza":
        pizza_id = request.form.get("pizza_id")
        if not pizza_id:
            flash("Select a pizza.", "error"); return redirect(url_for("orders.new_order"))
        price_row = db.session.execute(text(
            "SELECT price_ex_vat FROM v_pizza_price WHERE pizza_id = :pid"
        ), {"pid": pizza_id}).first()
        price_ex_vat = float(price_row[0]) if price_row else None
        db.session.add(OrderItem(order_id=order.order_id, pizza_id=pizza_id, quantity=qty, price_excl_vat=price_ex_vat))

    elif item_kind == "drink":
        drink_id = request.form.get("drink_id")
        if not drink_id:
            flash("Select a drink.", "error"); return redirect(url_for("orders.new_order"))
        price_row = db.session.execute(text(
            "SELECT price_ex_vat FROM v_drink_price WHERE drink_id = :did"
        ), {"did": drink_id}).first()
        price_ex_vat = float(price_row[0]) if price_row else 0.0
        db.session.add(OrderItem(order_id=order.order_id, drink_id=drink_id,
                                quantity=qty, price_excl_vat=price_ex_vat))

    elif item_kind == "dessert":
        dessert_id = request.form.get("dessert_id")
        if not dessert_id:
            flash("Select a dessert.", "error"); return redirect(url_for("orders.new_order"))
        price_row = db.session.execute(text(
            "SELECT price_ex_vat FROM v_dessert_price WHERE dessert_id = :did"
        ), {"did": dessert_id}).first()
        price_ex_vat = float(price_row[0]) if price_row else 0.0
        db.session.add(OrderItem(order_id=order.order_id, dessert_id=dessert_id,
                             quantity=qty, price_excl_vat=price_ex_vat))

    db.session.commit()
    flash("Order created.", "success")
    return redirect(url_for("orders.list_orders"))
