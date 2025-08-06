import psycopg2

PG_CONN_INFO = {
    "host": "اسم_المضيف.render.com",
    "dbname": "اسم_قاعدة_البيانات",
    "user": "اسم_المستخدم",
    "password": "كلمة_المرور",
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
