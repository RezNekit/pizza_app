from sqlalchemy import text
from datetime import datetime, timedelta
from models import db

def get_top_selling_pizzas(limit=10, days=None):
    sql = """ 
            SELECT p.pizza_id, p.name, SUM(oi.quantity) AS total_sold, ROUND(SUM(oi.quantity * oi.price_excl_vat), 2) AS total_revenue_excl_vat
            FROM OrderItem oi
            JOIN Pizza p ON p.pizza_id = oi.pizza_id
            JOIN Orders o ON o.order_id = oi.order_id
            WHERE oi.pizza_id IS NOT NULL AND o.cancelled_at IS NULL            
            """
    pars = {}

    if days:
        sql += " AND o.order_date >= :start_date"
        pars["start_date"] = datetime.now() - timedelta(days=days)

    sql += """ GROUP BY p.pizza_id, p.name
            ORDER BY total_sold DESC
            LIMIT :limit 
            """
    pars["limit"] = limit
    rows = db.session.execute(text(sql), pars).mappings().all()
    return [dict(row) for row in rows]


def get_undelivered_orders():
    sql = """ 
        SELECT 
        o.order_id, 
        o.order_date, 
        o.current_status, 
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name, 
        c.phone AS customer_phone,
        a.postal_code,
        COUNT(oi.order_item_id) AS item_count,
        SUM(oi.quantity) AS total_items,
        ROUND(SUM(oi.quantity * oi.price_excl_vat), 2) AS order_value_ex_vat,
        CASE 
            WHEN dp.delivery_person_id IS NOT NULL 
            THEN CONCAT(dp.first_name, ' ', dp.last_name)
            ELSE 'Not assigned'
        END AS driver_name

        FROM Orders o
        JOIN Customers c ON c.customer_id = o.customer_id
        LEFT JOIN Address a ON a.address_id = c.address_id
        LEFT JOIN Delivery_Person dp ON dp.delivery_person_id = o.delivery_person_id
        JOIN OrderItem oi ON oi.order_id = o.order_id
        WHERE o.delivered_at IS NULL AND o.cancelled_at IS NULL 
        GROUP BY o.order_id, o.order_date, o.current_status, c.first_name, c.last_name, c.phone, a.postal_code, dp.first_name, dp.last_name, dp.delivery_person_id
        ORDER BY o.order_date ASC
        """
    
    rows = db.session.execute(text(sql)).mappings().all()
    return [dict(row) for row in rows]

def get_monthly_earnings_by_gender(month=None, year=None):
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
        
    sql = """
        SELECT 
            c.gender, 
            COUNT(DISTINCT o.order_id) AS order_count, 
            ROUND(SUM(oi.quantity * oi.price_excl_vat), 2) AS total_revenue_excl_vat,
            ROUND(AVG(oi.quantity * oi.price_excl_vat), 2) AS avg_order_value
        FROM Orders o 
        JOIN Customers c ON c.customer_id = o.customer_id
        JOIN OrderItem oi ON oi.order_id = o.order_id
        WHERE strftime('%m', o.order_date) = :month 
          AND strftime('%Y', o.order_date) = :year 
          AND o.cancelled_at IS NULL
        GROUP BY c.gender
        ORDER BY total_revenue_excl_vat DESC
    """
    
    month_str = f"{month:02d}"
    rows = db.session.execute(text(sql), {"month": month_str, "year": str(year)}).mappings().all()
    return [dict(row) for row in rows]


def get_monthly_earnings_by_age(month=None, year=None):
    if month is None:
        month = datetime.now().month    
    if year is None:
        year = datetime.now().year
    
    sql = """ 
            SELECT 
                CASE 
                    WHEN (julianday('now') - julianday(c.birth_date)) / 365  < 25 THEN 'Under 25'
                    WHEN (julianday('now') - julianday(c.birth_date)) / 365 BETWEEN 25 AND 34 THEN '25-34'
                    WHEN (julianday('now') - julianday(c.birth_date)) / 365 BETWEEN 35 AND 44 THEN '35-44'
                    WHEN (julianday('now') - julianday(c.birth_date)) / 365 BETWEEN 45 AND 54 THEN '45-54'
                    ELSE '55+'
                END AS age_group,
                COUNT(DISTINCT o.order_id) AS order_count,
                ROUND(SUM(oi.quantity * oi.price_excl_vat), 2) AS total_revenue_excl_vat,
                COUNT(DISTINCT c.customer_id) AS unique_customers
            FROM Orders o
            JOIN Customers c ON c.customer_id = o.customer_id
            JOIN OrderItem oi ON oi.order_id = o.order_id
            WHERE strftime('%m', o.order_date) = :month AND strftime('%Y', o.order_date) = :year AND o.cancelled_at IS NULL AND c.birth_date IS NOT NULL
            GROUP BY age_group
            ORDER BY total_revenue_excl_vat DESC
        """
    month_str = f"{month:02d}"
    rows = db.session.execute(text(sql), {"month": month_str, "year": str(year)}).mappings().all()
    return [dict(row) for row in rows]


def get_monthly_earnings_by_postal_code(month=None, year=None, limit=10):
    if month is None:
        month = datetime.now().month    
    if year is None:
        year = datetime.now().year

    sql = """ 
        SELECT a.postal_code, a.city, COUNT(DISTINCT o.order_id) AS order_count, COUNT(DISTINCT c.customer_id) AS unique_customers, ROUND(SUM(oi.quantity * oi.price_excl_vat), 2) AS total_revenue_ex_vat
        FROM Orders o
        JOIN Customers c ON c.customer_id = o.customer_id
        JOIN Address a ON a.address_id = c.address_id
        JOIN OrderItem oi ON oi.order_id = o.order_id
        WHERE strftime('%m', o.order_date) = :month AND strftime('%Y', o.order_date) = :year AND o.cancelled_at IS NULL AND o.cancelled_at IS NULL
        GROUP BY a.postal_code, a.city
        ORDER BY total_revenue_ex_vat DESC
        LIMIT :limit
            """
    month_str = f"{month:02d}"
    rows = db.session.execute(text(sql), {"month": month_str, "year": str(year), "limit": limit}).mappings().all()


    return [dict(row) for row in rows]


