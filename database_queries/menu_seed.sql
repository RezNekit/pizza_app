-- menu_seed.sql
-- Idempotent seed for the Pizza app (MySQL 8+)
SET sql_mode = 'STRICT_ALL_TABLES';

START TRANSACTION;

-- ========================
-- Ingredients (21)  — upsert by UNIQUE(name)
-- ========================
INSERT INTO Ingredient (name, cost_per_one) VALUES
  ('Flour (100g)',             0.10),
  ('BBQ Sauce (50ml)',         0.15),
  ('Pepperoni',                0.30),
  ('Mozzarella (1 slice)',     0.30),
  ('Chicken',                  0.40),
  ('Turkey',                   0.45),
  ('Cheddar (1 slice)',        0.35),
  ('Parmesan (shavings)',      0.50),
  ('Gouda Cheese',             0.40),
  ('Pineapple',                0.25),
  ('Hot Honey (30ml)',         0.17),
  ('Bell Pepper (slice)',      0.20),
  ('Onion (ring)',             0.15),
  ('Olives (5 pcs)',           0.15),
  ('Mushrooms (3 pcs)',        0.20),
  ('Vegan Cheese',             0.50),
  ('Tuna',                     0.60),
  ('Veggie Chicken',           0.70),
  ('Jalapeno',                 0.12),
  ('Tomato Sauce (50ml)',      0.10),
  ('Cherry Tomato (5 pcs)',    0.20)
ON DUPLICATE KEY UPDATE
  cost_per_one = VALUES(cost_per_one);

-- ========================
-- Pizzas (10) — upsert by UNIQUE(name)
-- ========================
INSERT INTO Pizza (name, is_vegetarian, is_vegan) VALUES
  ('BBQ Meatlovers pizza', 0, 0),
  ('4 Cheese Pizza',       1, 0),
  ('Hawaii pizza',         0, 0),
  ('Pepperoni Hot Honey',  0, 0),
  ('New York Pizza',       0, 0),
  ('Vegan California',     1, 1),
  ('Tuna Treat Pizza',     0, 0),
  ('Spicy Indian Veggie',  1, 0),
  ('Magherita',            1, 0),
  ('Chicken Parmesan',     0, 0)
ON DUPLICATE KEY UPDATE
  is_vegetarian = VALUES(is_vegetarian),
  is_vegan      = VALUES(is_vegan);

-- ========================
-- Recipes — upsert via PK(pizza_id, ingredient_id)
-- ========================

-- Helper macro pattern (repeat per line):
-- INSERT INTO PizzaIngredient (...) SELECT ...
-- ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- BBQ Meatlovers pizza
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='BBQ Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 5 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='Pepperoni'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='Chicken'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='BBQ Meatlovers pizza' AND i.name='Turkey'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- 4 Cheese Pizza
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 4 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 4 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Cheddar (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Parmesan (shavings)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='4 Cheese Pizza' AND i.name='Gouda Cheese'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Hawaii pizza
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Hawaii pizza' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Hawaii pizza' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 10 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Hawaii pizza' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Hawaii pizza' AND i.name='Turkey'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Pepperoni Hot Honey
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Pepperoni Hot Honey' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Pepperoni Hot Honey' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Pepperoni Hot Honey' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 5 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Pepperoni Hot Honey' AND i.name='Pepperoni'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Pepperoni Hot Honey' AND i.name='Hot Honey (30ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- New York Pizza
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 4 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 4 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Bell Pepper (slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Onion (ring)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Olives (5 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Mushrooms (3 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Turkey'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='New York Pizza' AND i.name='Pineapple'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Vegan California
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Vegan Cheese'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Onion (ring)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Bell Pepper (slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Mushrooms (3 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Vegan California' AND i.name='Olives (5 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Tuna Treat Pizza
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Tuna'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Olives (5 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Tuna Treat Pizza' AND i.name='Onion (ring)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Spicy Indian Veggie
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Onion (ring)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Jalapeno'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Spicy Indian Veggie' AND i.name='Veggie Chicken'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Magherita
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Magherita' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Magherita' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 5 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Magherita' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- Chicken Parmesan
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Flour (100g)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 1 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Tomato Sauce (50ml)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 21 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Mozzarella (1 slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Onion (ring)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Chicken'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 3 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Parmesan (shavings)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 4 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Cherry Tomato (5 pcs)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
INSERT INTO PizzaIngredient (pizza_id, ingredient_id, quantity)
SELECT p.pizza_id, i.ingredient_id, 2 FROM Pizza p JOIN Ingredient i
 WHERE p.name='Chicken Parmesan' AND i.name='Bell Pepper (slice)'
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);

-- ========================
-- Drinks — upsert by UNIQUE(name,size_ml)
-- ========================
INSERT INTO Drink (name, size_ml, price_excl_vat) VALUES
  ('Cola',            330, 2.50),
  ('Cola Zero',       330, 2.50),
  ('Apple Juice',     250, 1.50),
  ('Sparkling Water', 500, 1.00),
  ('Still Water',     500, 1.00)
ON DUPLICATE KEY UPDATE
  price_excl_vat = VALUES(price_excl_vat);

-- ========================
-- Desserts — upsert by UNIQUE(name)
-- ========================
INSERT INTO Dessert (name, price_excl_vat) VALUES
  ('Tiramisu', 4.00),
  ('Panna Cotta', 3.00),
  ('Chocolate Mousse', 3.00),
  ('Cheesecake', 5.00)
ON DUPLICATE KEY UPDATE
  price_excl_vat = VALUES(price_excl_vat);

-- ========================
-- Customers — upsert by UNIQUE(email)
-- ========================
INSERT INTO Customers (first_name, last_name, birth_date, email, phone, gender) VALUES
  ('Tom','Pepels','1989-04-03','pepels@example.com','+310000002','M'),
  ('Kseniia','Patalakha','2006-06-22','ksusha@example.com','+310000001','F'),
  ('Mykyta','Reznikov','2005-11-17','methebest@example.com','+310000003','M'),
  ('Alex','Trutenko','2006-01-04','alwayslatw@example.com','+310000004','M'),
  ('Valentyn','Prianikov','2006-04-23','valyk@example.com','+310000005','M'),
  ('Evgueni','Smirnov','1985-07-30','smirnov@example.com','+310000006','M'),
  ('Grace','Young','1996-09-19','grace@example.com','+310000007','F'),
  ('Hank','Ford','1987-11-11','hank@example.com','+310000008','M'),
  ('Ivy','Klein','1999-03-07','ivy@example.com','+310000009','F'),
  ('Jake','Ng','1994-12-02','jake@example.com','+310000010','M')
ON DUPLICATE KEY UPDATE
  first_name = VALUES(first_name),
  last_name  = VALUES(last_name),
  birth_date = VALUES(birth_date),
  phone      = VALUES(phone),
  gender     = VALUES(gender);

-- ========================
-- Delivery persons — upsert by UNIQUE(phone)
-- ========================
INSERT INTO Delivery_Person (first_name, last_name, phone, status) VALUES
  ('Liam','Van Dijk','+319700001','active'),
  ('Noah','De Boer', '+319700002','active'),
  ('Mila','Jansen',  '+319700003','active')
ON DUPLICATE KEY UPDATE
  first_name = VALUES(first_name),
  last_name  = VALUES(last_name),
  status     = VALUES(status);

-- ========================
-- Delivery assignments — upsert by UNIQUE(delivery_person_id, postal_code)
-- (look up driver_id by phone to avoid assuming autoincrement values)
-- ========================

-- Liam → 6211, 6212
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6211'
FROM Delivery_Person dp WHERE dp.phone = '+319700001'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6212'
FROM Delivery_Person dp WHERE dp.phone = '+319700001'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);

-- Noah → 6221, 6222
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6221'
FROM Delivery_Person dp WHERE dp.phone = '+319700002'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6222'
FROM Delivery_Person dp WHERE dp.phone = '+319700002'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);

-- Mila → 6231, 6232
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6231'
FROM Delivery_Person dp WHERE dp.phone = '+319700003'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);
INSERT INTO DeliveryAssignment (delivery_person_id, postal_code)
SELECT dp.delivery_person_id, '6232'
FROM Delivery_Person dp WHERE dp.phone = '+319700003'
ON DUPLICATE KEY UPDATE postal_code = VALUES(postal_code);

COMMIT;
