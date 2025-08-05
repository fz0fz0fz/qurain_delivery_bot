def create_drivers_table_pg():
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_drivers_table_pg()
    print("تم إنشاء جدول السائقين في PostgreSQL بنجاح.")