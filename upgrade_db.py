import sqlite3

conn = sqlite3.connect('orders.db')
c = conn.cursor()

# إضافة عمود sent إذا لم يكن موجودًا
try:
    c.execute("ALTER TABLE orders ADD COLUMN sent INTEGER DEFAULT 0")
    print("تمت إضافة العمود sent بنجاح!")
except sqlite3.OperationalError:
    print("العمود sent موجود بالفعل.")

# إضافة عمود order_number إذا لم يكن موجودًا
try:
    c.execute("ALTER TABLE orders ADD COLUMN order_number TEXT")
    print("تمت إضافة العمود order_number بنجاح!")
except sqlite3.OperationalError:
    print("العمود order_number موجود بالفعل.")

conn.commit()
conn.close()