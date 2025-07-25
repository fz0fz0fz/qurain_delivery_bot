import sqlite3

conn = sqlite3.connect('orders.db')
c = conn.cursor()
c.execute("ALTER TABLE orders ADD COLUMN sent INTEGER DEFAULT 0")
conn.commit()
conn.close()
print("تمت إضافة العمود sent بنجاح!")