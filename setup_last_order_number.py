import psycopg2

PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432,
}

def setup_last_order_number_table():
    conn = psycopg2.connect(
        host=PG_CONN_INFO["host"],
        dbname=PG_CONN_INFO["dbname"],
        user=PG_CONN_INFO["user"],
        password=PG_CONN_INFO["password"],
        port=PG_CONN_INFO["port"]
    )
    cur = conn.cursor()
    # إنشاء الجدول إذا لم يكن موجودًا
    cur.execute("""
        CREATE TABLE IF NOT EXISTS last_order_number (
            id SERIAL PRIMARY KEY,
            last_number INTEGER NOT NULL
        );
    """)
    # التأكد من وجود صف البداية
    cur.execute("SELECT COUNT(*) FROM last_order_number;")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO last_order_number (last_number) VALUES (0);")
        print("✅ تم إنشاء الجدول وإضافة صف البداية.")
    else:
        print("ℹ️ الجدول موجود بالفعل ويوجد صف بداخله.")
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    setup_last_order_number_table()
