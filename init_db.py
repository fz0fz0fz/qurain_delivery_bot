import sqlite3

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

if __name__ == "__main__":
    init_db()
    print("Database tables created (if not exist).")