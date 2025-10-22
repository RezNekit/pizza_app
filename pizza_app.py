import os
from flask import Flask

from controllers import seed_data, create_views, get_pizza_menu, simple_method, get_full_menu
from models import db
from uilogic import menu_bp, customers_bp, orders_bp

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.json.sort_keys = False
    app.secret_key = "dev-secret"
    
    db.init_app(app)

    with app.app_context():
        if DATABASE_URL.startswith("sqlite:"):
            db.session.execute(db.text("PRAGMA foreign_keys = ON"))
            db.session.commit()

        print("Creating tables…")
        db.create_all()
        print("Seeding data…")
        seed_data()
        print("Creating views…")
        create_views()
        print("Startup complete.")

    app.register_blueprint(menu_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(orders_bp)


    @app.route("/")
    def index():
        return ('<h3>Pizza Project</h3>'
                '<p><a href="/pizzas">Pizzas</a> · '
                '<a href="/drinks">Drinks</a> · '
                '<a href="/desserts">Desserts</a> · '
                '<a href="/customers">Customers</a> · '
                '<a href="/orders">Orders</a> ·'
                '<a href="/reports">Reports</a> · '
                '<a href="/menu">Pizza Menu (RAW)</a> ·'
                '<a href="/menu/full">Full Menu (RAW)</a>')

    @app.get("/menu")
    def menu():
        return {"menu": get_pizza_menu()} 
    
    @app.get("/menu/full")
    def full_menu():
        return get_full_menu()  

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        rows = simple_method()
        print("Ingredients:", [r["name"] for r in rows])
    app.run(port = 8000,debug=True)

    
        