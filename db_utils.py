import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    # إنشاء الجدول مع عمود sent
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            service_name TEXT,
            order_text TEXT,
            created_at TEXT,
            sent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def save_order(user_id, service_name, order_text):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO orders (user_id, service_name, order_text, created_at, sent) VALUES (?, ?, ?, ?, ?)',
        (user_id, service_name, order_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0)
    )
    conn.commit()
    conn.close()

def get_unsent_orders(user_id):
    conn = sqlite3.connect('orders.db')
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
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.executemany("UPDATE orders SET sent = 1 WHERE id = ?", [(oid,) for oid in order_ids])
    conn.commit()
    conn.close()

def get_all_orders(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute(
        "SELECT id, service_name, order_text, created_at, sent FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    orders = c.fetchall()
    conn.close()
    return orders

# لا تنسَ استدعاء init_db() مرة واحدة عند تشغيل السيرفر أول مرة