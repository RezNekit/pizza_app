from datetime import date
from models import db, DiscountCode
import order_placement as op
from birthday_discount import to_date
def apply_discount_code(order, customer, code_str):
    code = (code_str or "").strip().upper()
    if not code:
        return 0.0, None, "invalid"

    dc = DiscountCode.query.filter(db.func.upper(DiscountCode.code) == code).first()
    if not dc:
        return 0.0, None, "invalid"

    today  = date.today()
    starts = to_date(getattr(dc, "valid_from", None) or getattr(dc, "starts_at", None))
    ends   = to_date(getattr(dc, "valid_to",   None) or getattr(dc, "expires_at", None))

    if starts and today < starts:
        return 0.0, None, "not_started"
    if ends and today > ends:
        return 0.0, None, "expired"

    subtotal = float(op.subtotal_calc(order))  # subtotal after freebies
    percent  = getattr(dc, "percent_off", None) or getattr(dc, "percentage", None)
    fixed    = getattr(dc, "amount_off",  None) or getattr(dc, "fixed_amount", None)

    amount = 0.0
    if percent is not None:
        try:
            amount += subtotal * float(percent) / 100.0
        except Exception:
            pass
    if fixed is not None:
        try:
            amount += float(fixed)
        except Exception:
            pass

    amount = round(max(0.0, min(amount, subtotal)), 2)
    if amount <= 0.0:
        return 0.0, None, "zero_value"

    dc_id = getattr(dc, "id", None) or getattr(dc, "discount_code_id", None)
    return amount, dc_id, ""
