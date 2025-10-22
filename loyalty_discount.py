import controllers as cntrl
import order_placement as op


def count_pizzas_in_order(order) -> int:
    #How many pizzas are in THIS order (sum of quantities)
    return sum(int(it.quantity or 0) for it in order.items if it.pizza_id)

def apply_loyalty_discount(order, customer) -> float:
    if not customer:
        return 0.0

    already = cntrl.count_pizzas_for_customer(customer.customer_id)
    in_this_order = count_pizzas_in_order(order)                
    if in_this_order <= 0:
        return 0.0

    before = already // 10
    after  = (already + in_this_order) // 10
    milestones_earned = max(0, after - before)

    if milestones_earned == 0:
        return 0.0

    return round(op.subtotal_calc(order) * 0.30 * milestones_earned, 2)
