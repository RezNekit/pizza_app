from datetime import date, timedelta
from models import db, Ingredient, Pizza, PizzaIngredient, Drink, Dessert, Customer, DeliveryPerson, DeliveryAssignment, Address, DiscountCode
from sqlalchemy import or_
def seed_data() -> None:
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

        # --- Addresses (create/reuse) ---
        addr_specs = {
            # code: (street,               city,        postal_code, country)
            "MST_VRIJTHOF":      ("Vrijthof 1",         "Maastricht", "6211AA", "Netherlands"),
            "MST_TAPIJN":        ("Tapijnkazerne 20",   "Maastricht", "6211AE", "Netherlands"),
            "MST_BOSCH":         ("Boschstraat 5",      "Maastricht", "6211AS", "Netherlands"),
            "MST_STATIONSSTRAAT":("Stationsstraat 10",  "Maastricht", "6221BT", "Netherlands"),
            "MST_JEKER":         ("Sint Bernardusstraat 12","Maastricht","6211HL","Netherlands"),
            "MST_WYCK":          ("Wycker Brugstraat 34","Maastricht","6221ED","Netherlands"),
            "MST_HEER":          ("Akersteenweg 100",   "Maastricht", "6227AE", "Netherlands"),
            "MST_SINTPIETER":    ("Cannerweg 80",       "Maastricht", "6213BA", "Netherlands"),
            "MST_BOSCH2":        ("Boschstraat 120",    "Maastricht", "6211AZ", "Netherlands"),
        }
        addr_obj = {}
        for code, (street, city, pc, country) in addr_specs.items():
            a = Address.query.filter_by(street=street, city=city, postal_code=pc, country=country).one_or_none()
            if not a:
                a = Address(street=street, city=city, postal_code=pc, country=country)
                db.session.add(a)
                db.session.flush()
            addr_obj[code] = a

        # --- Customers (now each has an address_id; 2 share the same address) ---
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

        # map each customer (by email) to an address code
        
        cust_to_addr = {
            "pepels@example.com":      "MST_VRIJTHOF",     
            "ksusha@example.com":      "MST_VRIJTHOF",     
            "methebest@example.com":   "MST_TAPIJN",
            "alwayslate@example.com":  "MST_BOSCH",
            "valyk@example.com":       "MST_STATIONSSTRAAT",
            "smirnov@example.com":     "MST_JEKER",
            "grace@example.com":       "MST_WYCK",
            "hank@example.com":        "MST_HEER",
            "ivy@example.com":         "MST_SINTPIETER",
            "jake@example.com":        "MST_BOSCH2",
        }

        for f, l, b, e, p, g in cust_specs:
            a = addr_obj[cust_to_addr[e]]
            existing = Customer.query.filter(
                or_(Customer.email == e, Customer.phone == p)
            ).one_or_none()
            if existing:
                # keep it idempotent; also attach/overwrite the address
                existing.first_name = f
                existing.last_name  = l
                existing.birth_date = date.fromisoformat(b)
                existing.gender     = g
                existing.address_id = a.address_id
            else:
                db.session.add(Customer(
                    first_name=f, last_name=l,
                    birth_date=date.fromisoformat(b),
                    email=e, phone=p, gender=g,
                    address_id=a.address_id
                ))


        drivers = [
            ("Liam","Van Dijk","+319700001","active", ["6211AE","6221BT"]),
            ("Noah","De Boer","+319700002","active", ["6211HL","6221ED"]),
            ("Mila","Jansen","+319700003","active", ["6227AE","6227AE"]),
            ("Emma","Visser","+319700004","inactive", ["6211AA","6211AS"]),
            ("Olivia","Smit","+319700005","active", ["6213BA","6211AZ"]),
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
                    
        discount_specs = [
            # Active codes
            ("WELCOME10", 10, date.today() - timedelta(days=30), date.today() + timedelta(days=60)),
            ("YMBMAFIA", 25, date.today() - timedelta(days=10), date.today() + timedelta(days=30)),
            ("GRADE10", 35, date.today() - timedelta(days=5), date.today() + timedelta(days=90)),
            
            # Future code (not started yet)
            ("FUTURE25", 25, date.today() + timedelta(days=7), date.today() + timedelta(days=50)),
            
            # Expired code
            ("EXPIRED20", 20, date.today() - timedelta(days=60), date.today() - timedelta(days=10)),
        ]
        
        for code, percent, start, end in discount_specs:
            existing = DiscountCode.query.filter_by(code=code).one_or_none()
            if not existing:
                db.session.add(DiscountCode(
                    code=code,
                    percentage_off=percent,
                    valid_from=start,
                    valid_to=end
                ))
        
        print("✓ Seeded discount codes:")
        for code, percent, start, end in discount_specs:
            status = "Active" if start <= date.today() <= end else ("Future" if start > date.today() else "Expired")
            print(f"  - {code}: {percent}% off ({status})")

