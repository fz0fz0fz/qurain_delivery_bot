import re
import psycopg2
from db_utils import PG_CONN_INFO

def normalize_phone(phone):
    phone = str(phone).strip()
    phone = phone.replace(" ", "").replace("-", "").replace("_", "")
    # لو يبدأ بـ 00، حولها لـ 966
    if phone.startswith("00"):
        phone = "966" + phone[2:]
    # لو يبدأ بـ 0، حولها لـ 966 (مثل 0501234567 -> 966501234567)
    elif phone.startswith("0"):
        phone = "966" + phone[1:]
    # لو يبدأ بـ +966
    elif phone.startswith("+966"):
        phone = "966" + phone[4:]
    return phone

def driver_exists(phone):
    phone = normalize_phone(phone)
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT id FROM drivers WHERE phone = %s", (phone,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_driver(name, phone, user_id):
    phone = normalize_phone(phone)
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

    phone_in_msg_norm = normalize_phone(phone_in_msg)
    phone_from_sender_norm = normalize_phone(phone_from_sender)

    if phone_in_msg_norm != phone_from_sender_norm:
        return "❌ رقم الهاتف في الرسالة لا يطابق رقمك في واتساب. الرجاء التأكد من إرسال رقمك الصحيح."

    if driver_exists(phone_from_sender_norm):
        return "✅ أنت مسجل مسبقًا كسائق لدينا."

    add_driver(name.strip(), phone_from_sender_norm, user_id)
    return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name.strip()}\nالرقم: {phone_from_sender_norm}"

def delete_driver_by_phone(phone):
    phone = normalize_phone(phone)
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("DELETE FROM drivers WHERE phone = %s", (phone,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return deleted > 0

def get_all_drivers():
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM drivers ORDER BY created_at DESC")
    drivers = cur.fetchall()
    cur.close()
    conn.close()
    return drivers