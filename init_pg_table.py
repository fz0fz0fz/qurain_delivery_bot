# init_pg_table.py

import psycopg2

PG_CONN_INFO = {
    "host": "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com",
    "dbname": "remainders",
    "user": "remainders_user",
    "password": "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr",
    "port": 5432,
}

def create_table():
    conn = psycopg2.connect(
        host=PG_CONN_INFO["host"],
        dbname=PG_CONN_INFO["dbname"],
        user=PG_CONN_INFO["user"],
        password=PG_CONN_INFO["password"],
        port=PG_CONN_INFO["port"]
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS last_order_number (
            id SERIAL PRIMARY KEY,
            last_number INTEGER NOT NULL
        );
    """)
    # تأكد من وجود صف واحد فقط
    cur.execute("SELECT COUNT(*) FROM last_order_number;")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO last_order_number (last_number) VALUES (0);")
    conn.commit()
    cur.close()
    conn.close()
    print("Table created and initialized!")

if __name__ == "__main__":
    create_table()
