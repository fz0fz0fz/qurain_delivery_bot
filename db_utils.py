import sqlite3
from datetime import datetime

# بيانات الاتصال بقاعدة بيانات PostgreSQL (للاستخدام لاحقاً في دوال PostgreSQL)
PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432,
}

DB_PATH = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # إنشاء جدول الطلبات
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            service_name TEXT,
            order_text TEXT,
            created_at TEXT,
            sent INTEGER DEFAULT 0,
            order_number TEXT
        )
    ''')
    # إنشاء جدول ربط الطلب بالمندوب
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_drivers (
            order_number TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_order(user_id, service_name, order_text, order_number=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT INTO orders (user_id, service_name, order_text, created_at, sent, order_number) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, service_name, order_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0, order_number)
    )
    conn.commit()
    conn.close()

def update_order_number(order_ids, order_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("UPDATE orders SET order_number = ? WHERE id = ?", [(order_number, oid) for oid in order_ids])
    conn.commit()
    conn.close()

def get_unsent_orders(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, service_name, order_text, created_at FROM orders WHERE user_id = ? AND sent = 0 ORDER BY created_at ASC",
        (user_id,)
    )
    orders = c.fetchall()
    conn.close()
    return orders

def mark_orders_as_sent(order_ids):
    if not order_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("UPDATE orders SET sent = 1 WHERE id = ?", [(oid,) for oid in order_ids])
    conn.commit()
    conn.close()

def get_user_id_by_order_number(order_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM orders WHERE order_number = ? LIMIT 1", (order_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_all_orders(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, service_name, order_text, created_at, sent, order_number FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    orders = c.fetchall()
    conn.close()
    return orders

#######################
# دوال جدول order_drivers
#######################

def assign_driver_to_order(order_number, driver_id):
    """
    تربط رقم الطلب بالمندوب في جدول order_drivers
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO order_drivers (order_number, driver_id)
        VALUES (?, ?)
    """, (order_number, driver_id))
    conn.commit()
    conn.close()

def get_driver_for_order(order_number):
    """
    ترجع رقم المندوب المرتبط بالطلب (إن وجد)
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT driver_id FROM order_drivers WHERE order_number = ?
    """, (order_number,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def get_orders_for_driver(driver_id):
    """
    ترجع قائمة أرقام الطلبات المرتبطة بمندوب معيّن
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT order_number FROM order_drivers WHERE driver_id = ?
    """, (driver_id,))
    results = c.fetchall()
    conn.close()
    return [row[0] for row in results]

# لا تنسَ استدعاء init_db() مرة واحدة عند تشغيل السيرفر أول مرة