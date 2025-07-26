import sqlite3
import logging

# إعداد التسجيل لعرض الرسائل في Render
logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect('orders.db')
c = conn.cursor()

# إضافة عمود sent إذا لم يكن موجودًا
try:
    c.execute("ALTER TABLE orders ADD COLUMN sent INTEGER DEFAULT 0")
    logging.info("✅ تمت إضافة العمود sent بنجاح!")
except sqlite3.OperationalError:
    logging.info("ℹ️ العمود sent موجود بالفعل.")

# إضافة عمود order_number إذا لم يكن موجودًا
try:
    c.execute("ALTER TABLE orders ADD COLUMN order_number TEXT")
    logging.info("✅ تمت إضافة العمود order_number بنجاح!")
except sqlite3.OperationalError:
    logging.info("ℹ️ العمود order_number موجود بالفعل.")

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