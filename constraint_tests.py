from sqlalchemy import text, exc
from models import db, Pizza, Ingredient, PizzaIngredient, Discount, DiscountCode, Customer


def test_vegetarian_pizza_invalid_ingredients():
    problems = []
    non_vegetarian_ingredients = ["Pepperoni", "Chicken", "Turkey", "Tuna"]
    placeholders_list = []

    ingredients_str = ", ".join([f"'{ing}'" for ing in non_vegetarian_ingredients])


    sql = f"""
        SELECT DISTINCT p.pizza_id, p.name, i.name
        FROM Pizza p 
        JOIN PizzaIngredient pi ON pi.pizza_id = p.pizza_id
        JOIN Ingredient i ON i.ingredient_id = pi.ingredient_id
        WHERE p.is_vegetarian = 1 AND i.name IN ({ingredients_str})
        """
    try:
        res = db.session.execute(text(sql))
        for i in res:
            problems.append({'pizza_id': i[0], 'pizza_name': i[1], 'ingredient': i[2], 'problem': 'Non vegeterian ingredient in vegeterian pizza.'})
    except Exception as e:
        problems.append({'pizza_id': None, 'pizza_name': 'Error', 'ingredient': 'N/A', 'problem': f'Problem occurred: {e}'})
    return problems

def test_negative_ingredients_prices():
    problems = []
    sql = """ 
        SELECT i.ingredient_id, name, cost_per_one
        FROM Ingredient i  
        WHERE cost_per_one < 0
            """
    
    try:
        res = db.session.execute(text(sql))
        for i in res:
            problems.append({'ingredient_id': i[0], 'ingredient_name': i[1], 'ingredient_cost': i[2], 'problem': 'Negitve price for ingredient.'})
    except Exception as e:
        problems.append({'ingredient_id': None, 'ingredient_name': None, 'ingredient_cost': None,'error': f'Problem occurred: {e}'})
    return problems

def test_reused_discounts():
    problems = []

    sql = """
        SELECT d.discount_code_id, dc.code, c.customer_id, COUNT(*)
        FROM Discount d
        JOIN DiscountCode dc ON dc.discount_code_id = d.discount_code_id
        JOIN Customers c ON c.customer_id = d.customer_id
        GROUP BY d.discount_code_id, dc.code, c.customer_id
        HAVING COUNT(*) > 1   
            """

    try:
        res = db.session.execute(text(sql))
        for i in res:
            problems.append({'discount_code_id': i[0], 'discount_code': i[1], 'customer_id': i[2], 'usage_count': i[3], 'problem': 'A discount code used more than once'})
    except Exception as e:
        print(e)
        problems.append({'discount_code_id': None, 'discount_code': None, 'customer_id': None, 'usage_count': None,'error': f'Problem occurred: {e}'})
    return problems


def calculate_problems():
    result = {
        'non_vegetarian_ingredients_violations': test_vegetarian_pizza_invalid_ingredients(),
        'negative_ingredient_prices': test_negative_ingredients_prices(),
        'reused_discount_codes': test_reused_discounts()
    }

    total_violations = 0
    for violations in result.values():
        total_violations = total_violations + len(violations)
    
    result['summary'] = {'total_violations': total_violations, 'status':'PASS' if total_violations == 0 else 'FAILED'}
    return result


