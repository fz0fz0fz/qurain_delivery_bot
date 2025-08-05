import re
import psycopg2
from db_utils import PG_CONN_INFO

def driver_exists(phone):
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT id FROM drivers WHERE phone = %s", (phone,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_driver(name, phone, user_id):
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO drivers (name, phone, user_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING
    """, (name, phone, user_id))
    conn.commit()
    cur.close()
    conn.close()

def handle_driver_registration(user_id, message):
    # مثال الرسالة المتوقعة: "سائق - أحمد - 966512345678"
    match = re.match(r"سائق(?: نقل| مشاوير)?\s*[-:،]?\s*([^\d\-]+)\s*[-:،]\s*(\d+)", message)
    if not match:
        # تحقق إذا أرسل اسمه فقط بدون رقم
        name_only = re.match(r"سائق(?: نقل| مشاوير)?\s*[-:،]?\s*([^\d\-]+)$", message)
        if name_only:
            return "❌ يجب عليك إرسال اسمك ورقم جوالك معاً بهذا الشكل: سائق - اسمك - رقمك"
        return None  # ليست رسالة تسجيل سائق

    name, phone_in_msg = match.groups()
    phone_from_sender = user_id.split("@")[0] if "@c.us" in user_id else user_id

    if phone_in_msg != phone_from_sender:
        return "❌ رقم الهاتف في الرسالة لا يطابق رقمك في واتساب. الرجاء التأكد من إرسال رقمك الصحيح."

    if driver_exists(phone_from_sender):
        return "✅ أنت مسجل مسبقًا كسائق لدينا."

    add_driver(name.strip(), phone_from_sender, user_id)
    return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name.strip()}\nالرقم: {phone_from_sender}"

def get_all_drivers():
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM drivers ORDER BY created_at DESC")
    drivers = cur.fetchall()
    cur.close()
    conn.close()
    return drivers