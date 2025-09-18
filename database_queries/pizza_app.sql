CREATE TABLE Address (
    address_id INT PRIMARY KEY AUTO_INCREMENT,
    street VARCHAR(256),
    city VARCHAR(64),
    postal_code VARCHAR(16),
    country VARCHAR(64) 
);

CREATE TABLE IF NOT EXISTS Customers (
  customer_id     INT PRIMARY KEY AUTO_INCREMENT,
  first_name      VARCHAR(64)  NOT NULL,
  last_name       VARCHAR(64)  NOT NULL,
  birth_date      DATE         NOT NULL,
  email           VARCHAR(128) NOT NULL UNIQUE,
  phone           VARCHAR(64)  NOT NULL UNIQUE,
  gender          CHAR(1)      NULL CHECK (gender IN ('M','F')),
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Delivery_Person (
  delivery_person_id INT PRIMARY KEY AUTO_INCREMENT,
  first_name         VARCHAR(64) NOT NULL,
  last_name          VARCHAR(64) NOT NULL,
  phone              VARCHAR(64) NOT NULL UNIQUE,
  status             VARCHAR(16) NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','inactive'))
) ;

CREATE TABLE IF NOT EXISTS Pizza (
  pizza_id        INT PRIMARY KEY AUTO_INCREMENT,
  name            VARCHAR(128) NOT NULL UNIQUE,
  is_vegetarian   BOOLEAN NOT NULL DEFAULT 0,
  is_vegan        BOOLEAN  NOT NULL DEFAULT 0
  is_spicy        BOOLEAN  NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Ingredient (
  ingredient_id   INT PRIMARY KEY AUTO_INCREMENT,
  name            VARCHAR(128) NOT NULL UNIQUE,
  cost_per_one    DECIMAL(10,2) NOT NULL CHECK (cost_per_one >= 0)
);

CREATE TABLE IF NOT EXISTS Dessert (
  dessert_id      INT PRIMARY KEY AUTO_INCREMENT,
  name            VARCHAR(128) NOT NULL UNIQUE,
  price_excl_vat  DECIMAL(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Drink (
  drink_id        INT PRIMARY KEY AUTO_INCREMENT,
  name            VARCHAR(128) NOT NULL,
  size_ml         INT NOT NULL CHECK (size_ml > 0),
  price_excl_vat  DECIMAL(10,2) NOT NULL DEFAULT 0,
  CONSTRAINT uq_drink_name_size UNIQUE (name, size_ml)
);

CREATE TABLE IF NOT EXISTS PizzaIngredient (
  pizza_id        INT NOT NULL,
  ingredient_id   INT NOT NULL,
  quantity        INT NOT NULL CHECK (quantity > 0),
  PRIMARY KEY (pizza_id, ingredient_id),
  CONSTRAINT fk_pi_pizza  FOREIGN KEY (pizza_id)      REFERENCES Pizza(pizza_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_pi_ing    FOREIGN KEY (ingredient_id)  REFERENCES Ingredient(ingredient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS Orders (
  order_id           INT PRIMARY KEY AUTO_INCREMENT,
  customer_id        INT NOT NULL,
  delivery_person_id INT NULL,
  order_date         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  current_status     VARCHAR(32) NOT NULL DEFAULT 'new',
  delivered_at       TIMESTAMP NULL,
  cancelled_at       TIMESTAMP NULL,
  CONSTRAINT fk_ord_cust FOREIGN KEY (customer_id)        REFERENCES Customers(customer_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_ord_driver FOREIGN KEY (delivery_person_id) REFERENCES Delivery_Person(delivery_person_id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS OrderItem (
  order_item_id    INT PRIMARY KEY AUTO_INCREMENT,
  order_id         INT NOT NULL,
  pizza_id         INT NULL,
  drink_id         INT NULL,
  dessert_id       INT NULL,
  quantity         INT NOT NULL CHECK (quantity > 0),
  price_excl_vat   DECIMAL(10,2) NOT NULL DEFAULT 0,
  CONSTRAINT fk_oi_order   FOREIGN KEY (order_id)  REFERENCES Orders(order_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_oi_pizza   FOREIGN KEY (pizza_id)  REFERENCES Pizza(pizza_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_oi_drink   FOREIGN KEY (drink_id)  REFERENCES Drink(drink_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_oi_dessert FOREIGN KEY (dessert_id)REFERENCES Dessert(dessert_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  -- exactly one of (pizza_id, drink_id, dessert_id)
  CONSTRAINT chk_one_kind CHECK (
    (pizza_id IS NOT NULL) + (drink_id IS NOT NULL) + (dessert_id IS NOT NULL) = 1
  )
);


CREATE TABLE IF NOT EXISTS DeliveryAssignment (
  id                 INT PRIMARY KEY AUTO_INCREMENT,
  delivery_person_id INT NOT NULL,
  postal_code        VARCHAR(16) NOT NULL,
  CONSTRAINT uq_da UNIQUE (delivery_person_id, postal_code),
  CONSTRAINT fk_da_driver FOREIGN KEY (delivery_person_id) REFERENCES Delivery_Person(delivery_person_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);



CREATE TABLE DiscountCode (
    discount_code_id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(32) UNIQUE NOT NULL,
    percentage_off DECIMAL(5, 2) CHECK (percentage_off >= 0 AND percentage_off <= 100),
    valid_from DATE,
    valid_to DATE
);

CREATE TABLE Discount(
    discount_id INT PRIMARY KEY AUTO_INCREMENT,
    discount_code_id INT NOT NULL,
    customer_id INT,
    order_id INT,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_disc_order
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
      ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_disc_code
    FOREIGN KEY (discount_code_id) REFERENCES DiscountCode(discount_code_id)
      ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_disc_customer
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
      ON UPDATE CASCADE ON DELETE SET NULL,

    UNIQUE(discount_code_id),

    CONSTRAINT fk_discount_order_customer FOREIGN KEY (order_id, customer_id)
        REFERENCES Orders (order_id, customer_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE BirthdayDiscount(
    birthday_discount_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    year INT NOT NULL,
    discount_code_id INT,
    freedrink_available  BOOLEAN NOT NULL DEFAULT TRUE,
    freepizza_available  BOOLEAN NOT NULL DEFAULT TRUE,
    

     CONSTRAINT fk_bd_customer
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
      ON UPDATE CASCADE ON DELETE CASCADE,
     CONSTRAINT fk_bd_code
    FOREIGN KEY (discount_code_id) REFERENCES DiscountCode(discount_code_id)
      ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT uq_birthday UNIQUE(customer_id, year)
);

CREATE TABLE LoyaltyEarning(
    loyalty_earning_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    earned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    count INT NOT NULL DEFAULT 0,
    order_id INT NOT NULL,


     CONSTRAINT fk_loyalty_customer
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
      ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_loyalty_order
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
      ON UPDATE CASCADE ON DELETE CASCADE,

    UNIQUE(customer_id, order_id),
    CONSTRAINT chk_loyalty_count CHECK (count >= 0)
);

DROP VIEW IF EXISTS v_pizza_price;
DROP VIEW IF EXISTS v_pizza_cost_ex_vat;
DROP VIEW IF EXISTS PizzaCost;
DROP VIEW IF EXISTS v_drink_price;
DROP VIEW IF EXISTS v_dessert_price;

CREATE VIEW v_pizza_cost_ex_vat AS
SELECT
  p.pizza_id,
  p.name AS pizza_name,
  SUM(pi.quantity * i.cost_per_one) AS cost_ex_vat
FROM Pizza p
JOIN PizzaIngredient pi ON pi.pizza_id = p.pizza_id
JOIN Ingredient i       ON i.ingredient_id = pi.ingredient_id
GROUP BY p.pizza_id, p.name;

CREATE VIEW v_pizza_price AS
SELECT
  c.pizza_id,
  c.pizza_name,
  ROUND(c.cost_ex_vat * 1.40, 2)        AS price_ex_vat,
  ROUND(c.cost_ex_vat * 1.40 * 1.09, 2) AS price_inc_vat
FROM v_pizza_cost_ex_vat c;

CREATE VIEW PizzaCost AS
SELECT pizza_id, pizza_name, cost_ex_vat AS total_cost
FROM v_pizza_cost_ex_vat;

-- Drinks & Desserts: keep price_excl_vat in table, compute inc-VAT (9%) here
CREATE VIEW v_drink_price AS
SELECT
  d.drink_id,
  d.name,
  d.size_ml,
  CAST(d.price_excl_vat AS DECIMAL(10,2)) AS price_ex_vat,
  ROUND(CAST(d.price_excl_vat AS DECIMAL(10,2)) * 1.09, 2) AS price_inc_vat
FROM Drink d;

CREATE VIEW v_dessert_price AS
SELECT
  ds.dessert_id,
  ds.name,
  CAST(ds.price_excl_vat AS DECIMAL(10,2)) AS price_ex_vat,
  ROUND(CAST(ds.price_excl_vat AS DECIMAL(10,2)) * 1.09, 2) AS price_inc_vat
FROM Dessert ds;
