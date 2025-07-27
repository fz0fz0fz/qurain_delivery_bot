import sqlite3
import logging

# إعداد التسجيل لعرض الرسائل في Render
logging.basicConfig(level=logging.INFO)

DB_PATH = 'orders.db'

def add_column_if_not_exists(cursor, table, column, col_type):
    # يتحقق إذا كان العمود موجودًا مسبقًا قبل محاولة إضافته
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        logging.info(f"✅ تمت إضافة العمود {column} بنجاح!")
    else:
        logging.info(f"ℹ️ العمود {column} موجود بالفعل.")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # إضافة الأعمدة الجديدة إذا لم تكن موجودة
    add_column_if_not_exists(c, "orders", "sent", "INTEGER DEFAULT 0")
    add_column_if_not_exists(c, "orders", "order_number", "TEXT")

    # إنشاء جدول ربط الطلب بالمندوب
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS order_drivers (
                order_number TEXT PRIMARY KEY,
                driver_id TEXT NOT NULL
            )
        """)
        logging.info("✅ تم إنشاء جدول order_drivers بنجاح!")
    except sqlite3.OperationalError as e:
        logging.error(f"❌ خطأ في إنشاء جدول order_drivers: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
