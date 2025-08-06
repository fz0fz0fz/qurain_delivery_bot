import psycopg2

PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432
}

def alter_table():
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("ALTER TABLE drivers ADD COLUMN description TEXT;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ تم تعديل جدول drivers بنجاح.")

if __name__ == "__main__":
    alter_table()
