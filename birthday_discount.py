from datetime import date, datetime, time
from models import db, Customer, Order, OrderItem, BirthdayDiscount

def to_date(x):
    #Normalize DB/seeded values to a datetime
    if not x:
        return None
    if isinstance(x, datetime):
        return x
    if isinstance(x, date):              # date -> datetime @ 00:00
        return datetime.combine(x, time.min)
    if isinstance(x, str):
        # allow common formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S",  # full timestamp
            "%Y-%m-%dT%H:%M:%S",  # ISO without tz
            "%Y-%m-%d",           # date-only
            "%d.%m.%Y",           # dd.mm.yyyy
            "%Y/%m/%d",           # yyyy/mm/dd
        ):
            try:
                return datetime.strptime(x.strip(), fmt)
            except ValueError:
                pass
    return None  # Unknown format -> treat as missing

def is_birthday_today(birth_date):
    #Check if birth_date (any format) matches today's month/day
    if not birth_date:
        return False
    
    # Normalize to datetime first
    bd = to_date(birth_date)
    if not bd:
        return False
    
    # Get today as date object for comparison
    today = date.today()
    
    # Compare month and day only
    # bd is a datetime, so use bd.month and bd.day
    return (bd.month, bd.day) == (today.month, today.day)

def birthday_row(customer_id: int):
    """Get or create the current-year BirthdayDiscount row."""
    yr = date.today().year
    bd = (BirthdayDiscount.query
          .filter_by(customer_id=customer_id, year=yr)
          .one_or_none())
    if bd is None:
        bd = BirthdayDiscount(customer_id=customer_id, year=yr)  # defaults: both True
        db.session.add(bd)
        db.session.flush()
    return bd

def cheapest_line(items):
    if not items:
        return None
    return min(items, key=lambda it: (float(it.price_excl_vat or 0.0), int(it.order_item_id or 0)))

def clone_free_unit(it: OrderItem):
    if it.quantity and it.quantity > 1 and float(it.price_excl_vat or 0.0) > 0.0:
        # reduce original, add a free 1-qty row of same item type
        it.quantity -= 1
        kwargs = dict(order_id=it.order_id, quantity=1, price_excl_vat=0.0)
        if it.pizza_id:   kwargs["pizza_id"]   = it.pizza_id
        if it.drink_id:   kwargs["drink_id"]   = it.drink_id
        if it.dessert_id: kwargs["dessert_id"] = it.dessert_id
        db.session.add(OrderItem(**kwargs))
    else:
        it.price_excl_vat = 0.0

def apply_birthday_freebies(order: Order, customer: Customer) -> dict:
    res = {"free_pizza": False, "free_drink": False, "amount_ex_vat": 0.0}
    if not customer or not is_birthday_today(customer.birth_date):
        return res

    bd = birthday_row(customer.customer_id)

    # Choose the cheapest pizza line
    if getattr(bd, "freepizza_available", False):
        pizzas = [it for it in order.items if it.pizza_id and float(it.price_excl_vat or 0.0) > 0.0]
        it = cheapest_line(pizzas)
        if it:
            res["amount_ex_vat"] += float(it.price_excl_vat or 0.0)
            clone_free_unit(it)
            bd.freepizza_available = False
            res["free_pizza"] = True

    # Choose the cheapest drink line
    if getattr(bd, "freedrink_available", False):
        drinks = [it for it in order.items if it.drink_id and float(it.price_excl_vat or 0.0) > 0.0]
        it = cheapest_line(drinks)
        if it:
            res["amount_ex_vat"] += float(it.price_excl_vat or 0.0)
            clone_free_unit(it)
            bd.freedrink_available = False
            res["free_drink"] = True

    return res