from sqlalchemy import text
from models import db
from seed_data import seed_data


def create_views() -> None:
    """(Re)create price views used by /menu: sum(costs) → +40% margin → +9% VAT."""
    with db.session.begin():
        # Drop in dependency order
        db.session.execute(text("DROP VIEW IF EXISTS v_pizza_price"))
        db.session.execute(text("DROP VIEW IF EXISTS PizzaCost"))
        db.session.execute(text("DROP VIEW IF EXISTS v_pizza_cost_ex_vat"))

        db.session.execute(text("DROP VIEW IF EXISTS v_drink_price"))
        db.session.execute(text("DROP VIEW IF EXISTS v_dessert_price"))

        # Base cost per pizza (ex VAT)
        db.session.execute(text("""
            CREATE VIEW v_pizza_cost_ex_vat AS
            SELECT
                p.pizza_id,
                p.name AS pizza_name,
                SUM(pi.quantity * i.cost_per_one) AS cost_ex_vat
            FROM Pizza p
            JOIN PizzaIngredient pi ON pi.pizza_id = p.pizza_id
            JOIN Ingredient i ON i.ingredient_id = pi.ingredient_id
            GROUP BY p.pizza_id, p.name
        """))

        # Apply 40% margin then 9% VAT
        db.session.execute(text("""
            CREATE VIEW v_pizza_price AS
            SELECT
                c.pizza_id,
                c.pizza_name,
                ROUND(c.cost_ex_vat * 1.40, 2)        AS price_ex_vat,
                ROUND(c.cost_ex_vat * 1.40 * 1.09, 2) AS price_inc_vat
            FROM v_pizza_cost_ex_vat c
        """))

        
        db.session.execute(text("""
            CREATE VIEW PizzaCost AS
            SELECT pizza_id, pizza_name, cost_ex_vat AS total_cost
            FROM v_pizza_cost_ex_vat
        """))

        db.session.execute(text("""
            CREATE VIEW v_drink_price AS
            SELECT
              d.drink_id,
              d.name,
              d.size_ml,
              CAST(d.price_excl_vat AS DECIMAL(10,2)) AS price_ex_vat,
              ROUND(CAST(d.price_excl_vat AS DECIMAL(10,2)) * 1.09, 2) AS price_inc_vat
            FROM Drink d
        """))

       
        db.session.execute(text("""
            CREATE VIEW v_dessert_price AS
            SELECT
              ds.dessert_id,
              ds.name,
              CAST(ds.price_excl_vat AS DECIMAL(10,2)) AS price_ex_vat,
              ROUND(CAST(ds.price_excl_vat AS DECIMAL(10,2)) * 1.09, 2) AS price_inc_vat
            FROM Dessert ds
        """))

def seeddata() -> None:
    """Seed initial data into the database."""
    seed_data()

def get_pizza_menu() -> list[dict]:
    sql = text("""
        SELECT p.pizza_id, p.pizza_name, price_ex_vat, price_inc_vat
        FROM v_pizza_price p
        ORDER BY p.pizza_id
    """)
    rows = db.session.execute(sql).mappings().all()
    return [dict(r) for r in rows]


def simple_method() -> list[dict]:
    return db.session.execute(text(
        "SELECT * FROM Ingredient ORDER BY cost_per_one DESC"
    )).mappings().all()

def get_full_menu() -> dict:
    pizzas_sql = text("""
        SELECT
        pr.pizza_id,
        pr.pizza_name,
        pr.price_ex_vat,
        pr.price_inc_vat,
        p.is_vegetarian,
        p.is_vegan,
        p.is_spicy            
        FROM v_pizza_price pr
        JOIN Pizza p ON p.pizza_id = pr.pizza_id
        ORDER BY p.pizza_id
        """)
    pizza_rows = [dict(r) for r in db.session.execute(pizzas_sql).mappings().all()]

    drinks = db.session.execute(text("""
        SELECT drink_id, name, size_ml, price_ex_vat, price_inc_vat
        FROM v_drink_price ORDER BY drink_id
    """)).mappings().all()

    desserts = db.session.execute(text("""
        SELECT dessert_id, name, price_ex_vat, price_inc_vat
        FROM v_dessert_price ORDER BY dessert_id
    """)).mappings().all()

    return {
        "pizzas": pizza_rows,
        "drinks": [dict(d) for d in drinks],
        "desserts": [dict(d) for d in desserts],
    }




def count_pizzas_for_customer(customer_id):
    """Return how many pizzas customer already bought (exclude cancelled orders)."""
    sql = """
        SELECT SUM(oi.quantity)
        FROM OrderItem oi
        JOIN Orders o ON o.order_id = oi.order_id
        WHERE o.customer_id = :cid
          AND oi.pizza_id IS NOT NULL
          AND o.cancelled_at IS NULL
    """
    row = db.session.execute(text(sql), {"cid": customer_id}).scalar()
    if row is None:
        return 0
    return int(row)
       
def mark_delivered(order_id):
    try:
        db.session.execute(text("""
            UPDATE Orders
            SET delivered_at = CURRENT_TIMESTAMP, current_status = 'delivered'
            WHERE order_id = :oid
        """), {"oid": order_id})
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

