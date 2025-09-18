from datetime import date
from sqlalchemy import text, or_
from models import db, Pizza, Ingredient, PizzaIngredient, Drink, Dessert, Customer, DeliveryPerson, DeliveryAssignment


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


def seed_data() -> None:
    """Minimal, idempotent seeds for Week-2 (ingredients, pizzas, recipes)."""
    with db.session.begin():
        ing_specs = [
            ("Flour (100g)", 0.10), ("BBQ Sauce (50ml)", 0.15),
            ("Pepperoni", 0.3), ("Mozzarella (1 slice)", 0.3), ("Chicken", 0.4), ("Turkey", 0.45),
            ("Cheddar (1 slice)", 0.35), ("Parmesan (shavings)", 0.5), ("Gouda Cheese", 0.4),
            ("Pineapple", 0.25), ("Hot Honey (30ml)", 0.17), ("Bell Pepper (slice)", 0.2), ("Onion (ring)", 0.15),
            ("Olives (5 pcs)", 0.15), ("Mushrooms (3 pcs)", 0.2), ("Vegan Cheese", 0.5),
            ("Tuna", 0.6), ("Veggie Chicken", 0.7), ("Jalapeno", 0.12), ("Tomato Sauce (50ml)", 0.1),
            ("Cherry Tomato (5 pcs)", 0.2)
        ]
        name_to_ing = {}
        for nm, cost in ing_specs:
            ing = Ingredient.query.filter_by(name=nm).one_or_none()
            if not ing:
                ing = Ingredient(name=nm, cost_per_one=cost)
                db.session.add(ing)
            name_to_ing[nm] = ing

        pizza_specs = [
            ("BBQ Meatlovers pizza", False, False, False),
            ("4 Cheese Pizza", True, False, False),
            ("Hawaii pizza", False, False, False),
            ("Pepperoni Hot Honey", False, False, True),
            ("New York Pizza", False, False, False),
            ("Vegan California", True, True, False),
            ("Tuna Treat Pizza", False, False, False),
            ("Spicy Indian Veggie", True, False, True),
            ("Magherita", True, False, False),
            ("Chicken Parmesan", False, False, False)
        ]
        name_to_pizza = {}
        for nm, veg, vegan, sp in pizza_specs:
            p = Pizza.query.filter_by(name=nm).one_or_none()
            if not p:
                p = Pizza(name=nm, is_vegetarian=veg, is_vegan=vegan, is_spicy=sp)
                db.session.add(p)
            name_to_pizza[nm] = p

        db.session.flush()  # ensure IDs

        def add_recipe(pizza_name, items):
            p = name_to_pizza[pizza_name]
            for ing_name, qty in items:
                i = name_to_ing[ing_name]
                exists = PizzaIngredient.query.filter_by(pizza_id=p.pizza_id, ingredient_id=i.ingredient_id).one_or_none()
                if not exists:
                    db.session.add(PizzaIngredient(pizza_id=p.pizza_id, ingredient_id=i.ingredient_id, quantity=qty))

        add_recipe("BBQ Meatlovers pizza", [
            ("Flour (100g)", 2), ("BBQ Sauce (50ml)", 1), ("Mozzarella (1 slice)", 2), ("Pepperoni", 5),
            ("Chicken", 2), ("Turkey", 2)
        ])
        add_recipe("4 Cheese Pizza", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 4), ("Cheddar (1 slice)", 4),
            ("Parmesan (shavings)", 2), ("Gouda Cheese", 2)
        ])
        add_recipe("Hawaii pizza", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 2), ("Mozzarella (1 slice)", 10), ("Turkey", 3)
        ])
        add_recipe("Pepperoni Hot Honey", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 3), ("Pepperoni", 5),
            ("Hot Honey (30ml)", 3)
        ])
        add_recipe("New York Pizza", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 4),
            ("Bell Pepper (slice)", 4), ("Onion (ring)", 3), ("Olives (5 pcs)", 1), ("Mushrooms (3 pcs)", 3),
            ("Turkey", 2), ("Pineapple", 2)
        ])
        add_recipe("Vegan California", [
            ("Flour (100g)", 2), ("Vegan Cheese", 2), ("Onion (ring)", 2), ("Bell Pepper (slice)", 2),
            ("Mushrooms (3 pcs)", 2), ("Olives (5 pcs)", 2) 
        ])
        add_recipe("Tuna Treat Pizza", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 3),
            ("Tuna", 2), ("Olives (5 pcs)", 2), ("Onion (ring)", 3)
        ])
        add_recipe("Spicy Indian Veggie", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 2),
            ("Onion (ring)", 3), ("Jalapeno", 2), ("Veggie Chicken", 2)
        ])
        add_recipe("Magherita", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 5)
        ])
        add_recipe("Chicken Parmesan", [
            ("Flour (100g)", 2), ("Tomato Sauce (50ml)", 1), ("Mozzarella (1 slice)", 21),
            ("Onion (ring)", 2), ("Chicken", 3), ("Parmesan (shavings)", 3), ("Cherry Tomato (5 pcs)", 4),
            ("Bell Pepper (slice)", 2)
        ])


        for nm, ml, pr in [("Cola",330, 2.5),("Cola Zero",330, 2.5),("Apple Juice",250, 1.5),("Sparkling Water",500, 1),("Still Water",500, 1)]:
            if not Drink.query.filter_by(name=nm, size_ml=ml, price_excl_vat = pr).one_or_none():
                db.session.add(Drink(name=nm, size_ml=ml, price_excl_vat = pr))

        for nm, pr in [("Tiramisu", 4), ("Panna Cotta", 3), ("Chocolate Mousse", 3), ("Cheesecake", 5)]:
            if not Dessert.query.filter_by(name=nm, price_excl_vat = pr).one_or_none():
                db.session.add(Dessert(name=nm, price_excl_vat = pr))

        cust_specs = [
            ("Tom","Pepels","1990-04-03","pepels@example.com","+310000002","M"),
            ("Kseniia","Patalakha","2006-06-22","ksusha@example.com","+310000001","F"),
            ("Mykyta","Reznikov","2005-11-17","methebest@example.com","+310000003","M"),
            ("Alex","Trutenko","2006-01-04","alwayslate@example.com","+310000004","M"),
            ("Valentyn","Prianikov","2006-04-23","valyk@example.com","+310000005","M"),
            ("Evgueni","Smirnov","1985-07-30","smirnov@example.com","+310000006","M"),

            ("Grace","Young","1996-09-19","grace@example.com","+310000007","F"),
            ("Hank","Ford","1987-11-11","hank@example.com","+310000008","M"),
            ("Ivy","Klein","1999-03-07","ivy@example.com","+310000009","F"),
            ("Jake","Ng","1994-12-02","jake@example.com","+310000010","M"),
        ]
        for f, l, b, e, p, g in cust_specs:
            existing = Customer.query.filter(
                or_(Customer.email == e, Customer.phone == p)
            ).one_or_none()
            if existing:
                # keep it idempotent: update fields if they changed
                existing.first_name = f
                existing.last_name  = l
                existing.birth_date = date.fromisoformat(b)
                existing.gender     = g
            else:
                db.session.add(Customer(
                    first_name=f, last_name=l,
                    birth_date=date.fromisoformat(b),
                    email=e, phone=p, gender=g
                ))

        drivers = [
            ("Liam","Van Dijk","+319700001","active", ["6211","6212"]),
            ("Noah","De Boer","+319700002","active", ["6221","6222"]),
            ("Mila","Jansen","+319700003","active", ["6231","6232"]),
        ]
        for fn,ln,ph,st,codes in drivers:
            dp = DeliveryPerson.query.filter_by(phone=ph).one_or_none()
            if not dp:
                dp = DeliveryPerson(first_name=fn,last_name=ln,phone=ph,status=st)
                db.session.add(dp)
                db.session.flush()
            # assignments
            for pc in codes:
                if not DeliveryAssignment.query.filter_by(delivery_person_id=dp.delivery_person_id, postal_code=pc).one_or_none():
                    db.session.add(DeliveryAssignment(delivery_person_id=dp.delivery_person_id, postal_code=pc))


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
    """Week-3: full menu → pizzas (with veg/vegan labels + prices), drinks, desserts."""
    # pizzas_sql = text("""
    #     SELECT
    #       pr.pizza_id,
    #       pr.pizza_name,
    #       pr.price_ex_vat,
    #       pr.price_inc_vat,
    #       p.is_vegetarian,
    #       p.is_vegan
    #     FROM v_pizza_price pr
    #     JOIN Pizza p ON p.pizza_id = pr.pizza_id
    #     ORDER BY pr.pizza_id
    # """)
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
