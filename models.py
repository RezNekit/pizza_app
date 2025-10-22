from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    CheckConstraint, UniqueConstraint, ForeignKey, ForeignKeyConstraint,
)
from sqlalchemy.dialects.mysql import DECIMAL as MYSQL_DECIMAL 

db = SQLAlchemy()

class Address(db.Model):
    __tablename__ = "Address"
    address_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    street     = db.Column(db.String(256))
    city       = db.Column(db.String(64))
    postal_code= db.Column(db.String(16))
    country    = db.Column(db.String(64))

class Customer(db.Model):
    __tablename__ = "Customers"
    __table_args__ = (
        CheckConstraint(
            "birth_date IS NULL OR birth_date <= CURRENT_DATE",
            name="chk_birthdate_past"
        ),
    )
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name  = db.Column(db.String(64))
    last_name   = db.Column(db.String(64))
    birth_date  = db.Column(db.Date)
    email       = db.Column(db.String(128), unique=True, nullable=False)
    phone       = db.Column(db.String(15),   unique=True, nullable=False)
    gender      = db.Column(db.String(1))
    address_id  = db.Column(
        db.Integer,
        ForeignKey("Address.address_id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )

    address  = db.relationship("Address")
    orders   = db.relationship("Order", back_populates="customer")

class DeliveryPerson(db.Model):
    __tablename__ = "Delivery_Person"
    delivery_person_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(64))
    last_name  = db.Column(db.String(64))
    phone      = db.Column(db.String(15), unique=True, nullable=False)
    status     = db.Column(db.String(64))

    assignments = db.relationship("DeliveryAssignment", back_populates="driver")
    orders      = db.relationship("Order", back_populates="driver")

class Pizza(db.Model):
    __tablename__ = "Pizza"
    pizza_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name     = db.Column(db.String(64), nullable=False)
    is_vegetarian = db.Column(db.Boolean, default=False)  
    is_vegan      = db.Column(db.Boolean, default=False)
    is_spicy      = db.Column(db.Boolean, default=False)  

    ingredients = db.relationship("PizzaIngredient", back_populates="pizza")
    order_items = db.relationship("OrderItem", back_populates="pizza")

    def __repr__(self):
        return f"<Pizza {self.pizza_id} {self.name}>"


class Ingredient(db.Model):
    __tablename__ = "Ingredient"
    __table_args__ = (
        CheckConstraint("cost_per_one > 0", name="chk_cost_positive"),
    )
    ingredient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name          = db.Column(db.String(64), nullable=False)
    
    cost_per_one  = db.Column(db.Numeric(10, 2), nullable=False)

    pizzas = db.relationship("PizzaIngredient", back_populates="ingredient")

    def __repr__(self):
        return f"<Ingredient {self.ingredient_id} {self.name}>"
    
class Dessert(db.Model):
    __tablename__ = "Dessert"
    dessert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(64), nullable=False)
    price_excl_vat = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    order_items = db.relationship("OrderItem", back_populates="dessert")

class Drink(db.Model):
    __tablename__ = "Drink"
    __table_args__ = (
        CheckConstraint("size_ml > 0", name="chk_drink_ml"),
    )
    drink_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name     = db.Column(db.String(64), nullable=False)
    size_ml  = db.Column(db.Integer, nullable=False)
    price_excl_vat = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    order_items = db.relationship("OrderItem", back_populates="drink")

class PizzaIngredient(db.Model):
    __tablename__ = "PizzaIngredient"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_pi_qty_positive"),
        db.PrimaryKeyConstraint("pizza_id", "ingredient_id"),
        ForeignKeyConstraint(
            ["pizza_id"], ["Pizza.pizza_id"],
            onupdate="CASCADE", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["ingredient_id"], ["Ingredient.ingredient_id"],
            onupdate="CASCADE", ondelete="RESTRICT"
        ),
    )
    pizza_id      = db.Column(db.Integer, nullable=False)
    ingredient_id = db.Column(db.Integer, nullable=False)
    quantity      = db.Column(db.Integer, nullable=False)

    pizza      = db.relationship("Pizza", back_populates="ingredients")
    ingredient = db.relationship("Ingredient", back_populates="pizzas")

    def __repr__(self):
        return f"<PizzaIngredient pizza={self.pizza_id} ingredient={self.ingredient_id}>"
    
class Order(db.Model):
    __tablename__ = "Orders"
    __table_args__ = (
        UniqueConstraint("order_id", "customer_id", name="uq_order_id_customer"),
    )
    order_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id= db.Column(
        db.Integer,
        ForeignKey("Customers.customer_id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )
    delivery_person_id = db.Column(
        db.Integer,
        ForeignKey("Delivery_Person.delivery_person_id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )
    order_date     = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    current_status = db.Column(db.String(32))  # nullable like SQL
    delivered_at   = db.Column(db.DateTime, nullable=True)
    cancelled_at   = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer", back_populates="orders")
    driver   = db.relationship("DeliveryPerson", back_populates="orders")
    items    = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = "OrderItem"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_oi_qty_positive"),
        # Exactly one of (pizza_id, dessert_id, drink_id) must be NOT NULL:
        CheckConstraint(
            "((pizza_id IS NOT NULL) + (dessert_id IS NOT NULL) + (drink_id IS NOT NULL)) = 1",
            name="chk_one_item_type"
        ),
        ForeignKeyConstraint(
            ["order_id"], ["Orders.order_id"],
            onupdate="CASCADE", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["pizza_id"], ["Pizza.pizza_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
        ForeignKeyConstraint(
            ["dessert_id"], ["Dessert.dessert_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
        ForeignKeyConstraint(
            ["drink_id"], ["Drink.drink_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
    )
    order_item_id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id       = db.Column(db.Integer, nullable=False)
    quantity       = db.Column(db.Integer, nullable=False, default=1)
    price_excl_vat = db.Column(db.Numeric(10, 2), nullable=False)

    pizza_id   = db.Column(db.Integer, nullable=True)
    dessert_id = db.Column(db.Integer, nullable=True)
    drink_id   = db.Column(db.Integer, nullable=True)

    order   = db.relationship("Order", back_populates="items")
    pizza   = db.relationship("Pizza", back_populates="order_items")
    dessert = db.relationship("Dessert", back_populates="order_items")
    drink   = db.relationship("Drink", back_populates="order_items")

class DeliveryAssignment(db.Model):
    __tablename__ = "DeliveryAssignment"
    delivery_assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    delivery_person_id = db.Column(
        db.Integer,
        ForeignKey("Delivery_Person.delivery_person_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )
    postal_code = db.Column(db.String(16), nullable=False)
    active_from = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    active_to   = db.Column(db.DateTime)

    driver = db.relationship("DeliveryPerson", back_populates="assignments")

class DiscountCode(db.Model):
    __tablename__ = "DiscountCode"
    discount_code_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code         = db.Column(db.String(32), unique=True, nullable=False)
    percentage_off = db.Column(db.Numeric(5, 2), nullable=True)
    valid_from   = db.Column(db.Date)
    valid_to     = db.Column(db.Date)

class Discount(db.Model):
    __tablename__ = "Discount"
    __table_args__ = (
        UniqueConstraint("discount_code_id", "customer_id", name="uniq_discount_per_customer"),
        ForeignKeyConstraint(
            ["order_id"], ["Orders.order_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
        ForeignKeyConstraint(
            ["discount_code_id"], ["DiscountCode.discount_code_id"],
            onupdate="CASCADE", ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["customer_id"], ["Customers.customer_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
        # composite FK (order_id, customer_id) → Orders(order_id, customer_id)
        ForeignKeyConstraint(
            ["order_id", "customer_id"], ["Orders.order_id", "Orders.customer_id"],
            onupdate="CASCADE", ondelete="SET NULL",
            name="fk_discount_order_customer"
        ),
    )
    discount_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    discount_code_id = db.Column(db.Integer, nullable=False)
    customer_id      = db.Column(db.Integer, nullable=True)
    order_id         = db.Column(db.Integer, nullable=True)
    applied_at       = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)

class BirthdayDiscount(db.Model):
    __tablename__ = "BirthdayDiscount"
    __table_args__ = (
        UniqueConstraint("customer_id", "year", name="uq_birthday"),
        ForeignKeyConstraint(
            ["customer_id"], ["Customers.customer_id"],
            onupdate="CASCADE", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["discount_code_id"], ["DiscountCode.discount_code_id"],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
    )
    birthday_discount_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id   = db.Column(db.Integer, nullable=False)
    year          = db.Column(db.Integer, nullable=False)
    discount_code_id = db.Column(db.Integer, nullable=True)
    freedrink_available = db.Column(db.Boolean, nullable=False, default=True)
    freepizza_available = db.Column(db.Boolean, nullable=False, default=True)

class LoyaltyEarning(db.Model):
    __tablename__ = "LoyaltyEarning"
    __table_args__ = (
        UniqueConstraint("customer_id", "order_id", name="uq_loyalty_customer_order"),
        CheckConstraint("count >= 0", name="chk_loyalty_count"),
        ForeignKeyConstraint(
            ["customer_id"], ["Customers.customer_id"],
            onupdate="CASCADE", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["order_id"], ["Orders.order_id"],
            onupdate="CASCADE", ondelete="CASCADE"
        ),
    )
    loyalty_earning_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, nullable=False)
    earned_at   = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    count       = db.Column(db.Integer, nullable=False, default=0)
    order_id    = db.Column(db.Integer, nullable=False)
