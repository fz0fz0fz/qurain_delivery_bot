import psycopg2
import sqlite3
from datetime import datetime

# --- إعدادات اتصال PostgreSQL (العمال) ---
PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432,
}

def get_pg_conn():
    return psycopg2.connect(
        host=PG_CONN_INFO['host'],
        dbname=PG_CONN_INFO['dbname'],
        user=PG_CONN_INFO['user'],
        password=PG_CONN_INFO['password'],
        port=PG_CONN_INFO['port']
    )

# ========================
# دوال PostgreSQL (العمال)
# ========================

def insert_worker(section, name, phone):
    conn = get_pg_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO workers (section, name, phone) VALUES (%s, %s, %s)",
        (section, name, phone)
    )
    conn.commit()
    conn.close()

def get_workers_by_section(section):
    conn = get_pg_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, phone FROM workers WHERE section = %s ORDER BY id ASC", 
        (section,)
    )
    results = c.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "phone": row[2]} for row in results]

def is_worker_phone(phone):
    conn = get_pg_conn()
    c = conn.cursor()
    patterns = [phone, phone.replace("966", "0", 1), phone.replace("0", "966", 1)]
    c.execute(
        "SELECT COUNT(*) FROM workers WHERE phone = %s OR phone = %s OR phone = %s", 
        (patterns[0], patterns[1], patterns[2])
    )
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def delete_worker(worker_id):
    conn = get_pg_conn()
    c = conn.cursor()
    c.execute(
        "DELETE FROM workers WHERE id = %s", (worker_id,)
    )
    conn.commit()
    conn.close()

# =======================
# إعدادات SQLite (الطلبات)
# =======================

DB_PATH = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_drivers (
            order_number TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL
        )
    ''')
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

def assign_driver_to_order(order_number, driver_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO order_drivers (order_number, driver_id)
        VALUES (?, ?)
    """, (order_number, driver_id))
    conn.commit()
    conn.close()

def get_driver_for_order(order_number):
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT order_number FROM order_drivers WHERE driver_id = ?
    """, (driver_id,))
    results = c.fetchall()
    conn.close()
    return [row[0] for row in results]

# --- تأكد من تهيئة قاعدة بيانات SQLite عند بدء التشغيل ---
init_db()