# pg_utils.py

import psycopg2

PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432,
}

def get_pg_connection():
    return psycopg2.connect(
        host=PG_CONN_INFO["host"],
        dbname=PG_CONN_INFO["dbname"],
        user=PG_CONN_INFO["user"],
        password=PG_CONN_INFO["password"],
        port=PG_CONN_INFO["port"]
    )

def get_last_order_number_pg():
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT last_number FROM last_order_number ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    else:
        # إذا لم يوجد صف، أضفه لأول مرة
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO last_order_number (last_number) VALUES (0);")
        conn.commit()
        cur.close()
        conn.close()
        return 0

def generate_order_id_pg():
    conn = get_pg_connection()
    cur = conn.cursor()
    # جلب الرقم الأخير
    cur.execute("SELECT last_number FROM last_order_number ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    last_num = row[0] if row else 0
    new_num = last_num + 1
    # تحديث الرقم الأخير في الجدول
    cur.execute("UPDATE last_order_number SET last_number = %s WHERE id = (SELECT id FROM last_order_number ORDER BY id DESC LIMIT 1);", (new_num,))
    conn.commit()
    cur.close()
    conn.close()
    # توليد رقم الطلب بنفس التنسيق
    order_id = f"G{new_num:03d}"
    return order_id
