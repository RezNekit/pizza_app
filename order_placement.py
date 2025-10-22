from datetime import date, datetime, timedelta
from sqlalchemy import text
from models import db, Customer, Order, OrderItem, DiscountCode, Discount, LoyaltyEarning
import birthday_discount as bd
import loyalty_discount as ld
import traceback

VAT_RATE = 1.09 #this is our VAT rate

def get_item_price(item_type, item_id):
    view_map = {
        "pizza": "v_pizza_price",
        "drink": "v_drink_price", 
        "dessert": "v_dessert_price"
    }
    
    view = view_map.get(item_type)
    if not view:
        return 0.0
    
    id_col = f"{item_type}_id"
    price = db.session.execute(
        text(f"SELECT price_ex_vat FROM {view} WHERE {id_col} = :id"),
        {"id": item_id}
    ).scalar()
    
    return float(price or 0.0)


def add_order_items(order, items):
    #Add items to order and return them
    for it in (items or []):
        typ = (it.get("type") or "").strip().lower()
        
        try:
            qty = int(it.get("qty", 1))
        except Exception:
            qty = 1
            
        if qty <= 0:
            continue
        
        if typ not in ["pizza", "drink", "dessert"]:
            continue
            
        price = get_item_price(typ, it["id"])
        
        item_data = {
            "order_id": order.order_id,
            f"{typ}_id": it["id"],
            "quantity": qty,
            "price_excl_vat": price
        }
        
        db.session.add(OrderItem(**item_data))
    
    db.session.flush()


def subtotal_calc(order):
    #Compute subtotal (sum of price_excl_vat * qty) for order items
    total = sum(float(item.price_excl_vat) * int(item.quantity) for item in order.items)
    return round(total, 2)


def apply_birthday_discount(order, customer):
    pre_subtotal = subtotal_calc(order)
    freebies = bd.apply_birthday_freebies(order, customer)
    post_subtotal = subtotal_calc(order)
    
    discount_amount = round(max(0.0, pre_subtotal - post_subtotal), 2)
    
    return discount_amount, freebies


def record_loyalty_earning(order, customer_id):
    
    pizza_count = db.session.execute(
        text("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM OrderItem
            WHERE order_id = :oid AND pizza_id IS NOT NULL
        """),
        {"oid": order.order_id}
    ).scalar() or 0
    
    if int(pizza_count) > 0:
        db.session.add(
            LoyaltyEarning(
                customer_id=customer_id,
                order_id=order.order_id,
                count=int(pizza_count)
            )
        )


def apply_loyalty_discount(order, customer):
    loyalty_amount = float(ld.apply_loyalty_discount(order, customer) or 0.0)
    return loyalty_amount


def parse_date_field(value):
    """Parse date field from various formats."""
    if not value:
        return None
        
    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()
    
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except (ValueError, AttributeError):
            return None
    
    return None


def validate_discount_code(discount_code, customer_id, post_subtotal):
    code_upper = discount_code.upper()
    
    dc = DiscountCode.query.filter(
        db.func.upper(DiscountCode.code) == code_upper
    ).first()
    
    if not dc:
        return False, 0.0, "invalid"
    
    
    dc_id = getattr(dc, "id", None) or getattr(dc, "discount_code_id", None)
    
    # Check if customer already used this code
    already_used = db.session.execute(
        text("SELECT COUNT(*) FROM Discount WHERE discount_code_id = :dcid AND customer_id = :cid"),
        {"dcid": dc_id, "cid": customer_id}
    ).scalar() or 0
    
    if already_used > 0:
        return False, 0.0, "already_used"
    
    # Parse dates
    today = date.today()
    starts_dt = parse_date_field(getattr(dc, "valid_from", None) or getattr(dc, "starts_at", None))
    ends_dt = parse_date_field(getattr(dc, "valid_to", None) or getattr(dc, "expires_at", None))
    
    print(f"  valid_from: {starts_dt}, valid_to: {ends_dt}, today: {today}")
    
    # Check date validity
    if starts_dt and today < starts_dt:
        return False, 0.0, "not_started"
    
    if ends_dt and today > ends_dt:
        return False, 0.0, "expired"
    
    # Check usage limit (total uses across all customers)
    max_uses = getattr(dc, "max_uses", None) or getattr(dc, "usage_limit", None)
    
    if max_uses is not None:
        used_count = db.session.execute(
            text("SELECT COUNT(*) FROM Discount WHERE discount_code_id = :id"),
            {"id": dc_id}
        ).scalar() or 0
        
        if int(used_count) >= int(max_uses):
            print(f"✗ Code exhausted ({used_count}/{max_uses})")
            return False, 0.0, "exhausted"
    
    # Calculate discount amount
    percent = getattr(dc, "percent_off", None) or getattr(dc, "percentage", None) or getattr(dc, "percentage_off", None)
    fixed = getattr(dc, "amount_off", None) or getattr(dc, "fixed_amount", None)
    
    amount = 0.0
    if percent is not None:
        try:
            amount += post_subtotal * float(percent) / 100.0
        except Exception:
            pass
    
    if fixed is not None:
        try:
            amount += float(fixed)
        except Exception:
            pass
    
    amount = round(max(0.0, min(amount, post_subtotal)), 2)
    
    if amount <= 0.0:
        return False, 0.0, "zero_value"
    
    return True, amount, ""

def apply_discount_code(discount_code, customer_id, order, post_subtotal):
    #Process discount code and record if valid.
    code_entered = discount_code.strip()
    
    if not code_entered:
        return False, 0.0, "", ""
    
    code_applied, code_amount, code_reason = validate_discount_code(
        code_entered, customer_id, post_subtotal
    )
    
    if code_applied:
        dc = DiscountCode.query.filter(
            db.func.upper(DiscountCode.code) == code_entered.upper()
        ).first()
        
        dc_id = getattr(dc, "id", None) or getattr(dc, "discount_code_id", None)
        
        db.session.add(
            Discount(
                discount_code_id=dc_id,
                customer_id=customer_id,
                order_id=order.order_id
            )
        )
    
    return code_applied, code_amount, code_entered, code_reason


def assign_delivery_person(order, customer):
    #Assign a delivery person by postal code with 30-minute cooldown
    if not customer or not customer.address or not customer.address.postal_code:
        order.current_status = "pending-driver"
        return
    
    pc = customer.address.postal_code
    
    # Get drivers for postal code
    rows = db.session.execute(
        text("SELECT da.delivery_person_id FROM DeliveryAssignment da WHERE da.postal_code = :pc"),
        {"pc": pc}
    ).fetchall()
    
    if not rows:
        order.current_status = "pending-driver"
        return
    
    # Find available driver (30-minute cooldown)
    cutoff = datetime.now() - timedelta(minutes=30)
    available_driver = None
    
    for r in rows:
        driver_id = r[0]
        last = db.session.execute(
            text("SELECT MAX(delivered_at) FROM Orders WHERE delivery_person_id = :did"),
            {"did": driver_id}
        ).scalar()
        
        # Normalize to datetime
        if last is not None:
            if isinstance(last, str):
                try:
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            last = datetime.strptime(last, fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    last = None
            elif isinstance(last, date) and not isinstance(last, datetime):
                last = datetime.combine(last, datetime.min.time())
        
        if last is None or last < cutoff:
            available_driver = driver_id
            break
    
    if available_driver:
        order.delivery_person_id = available_driver
        order.current_status = "assigned"
    else:
        order.current_status = "pending-driver"


def place_order(customer_id, items, discount_code=None):
    
    #Create order with items, apply discounts, assign delivery person.

    try:
        # Validate customer
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValueError("Customer not found.")
        
        # Create order
        order = Order(customer_id=customer_id, current_status="new")
        db.session.add(order)
        db.session.flush()
        
        # Add items
        add_order_items(order, items)
        
        # Apply birthday discount
        birthday_amount, freebies = apply_birthday_discount(order, customer)
        
        # Get post-birthday subtotal
        post_subtotal = subtotal_calc(order)
        
        # Record loyalty earning
        record_loyalty_earning(order, customer_id)
        
        # Apply loyalty discount
        loyalty_amount = apply_loyalty_discount(order, customer)
        
        # Apply discount code
        code_applied, code_amount, code_entered, code_reason = apply_discount_code(
            discount_code or "", customer_id, order, post_subtotal
        )
        
        # Assign delivery person
        assign_delivery_person(order, customer)
        
        # Calculate finals
        subtotal = float(post_subtotal)
        total_discount = round(float(birthday_amount) + float(loyalty_amount) + float(code_amount), 2)
        final_total = round(max(0.0, subtotal - (float(loyalty_amount) + float(code_amount))), 2)
        
        final_total_inc_vat = round(final_total * VAT_RATE, 2)
        
        db.session.commit()
        
        # Return summary
        return {
            "order_id": order.order_id,
            "subtotal_ex_vat": round(subtotal, 2),
            "discounts_ex_vat": total_discount,
            "total_ex_vat": final_total,
            "total_inc_vat": final_total_inc_vat,
            "vat_rate": VAT_RATE, 
            "vat_amount": round(final_total_inc_vat - final_total, 2),
            "freebies": freebies,
            "status": order.current_status,
            "driver_id": order.delivery_person_id,
            "code_applied": bool(code_applied),
            "code_amount": round(float(code_amount), 2),
            "code_entered": code_entered,
            "code_reason": code_reason,
        }
    
    except Exception as e:
        db.session.rollback()
        print(f"\n{'='*60}")
        print(f"✗ FATAL ERROR IN place_order")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise