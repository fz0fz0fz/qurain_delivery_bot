# workers_register.py
import psycopg2
from send_utils import send_message
from pg_utils import get_pg_connection

# الحالات الخاصة بالعمال
WORKER_STATES = [
    "awaiting_worker_register",
    "awaiting_worker_name",
    "awaiting_worker_phone",
    "awaiting_worker_description",
    "awaiting_worker_delete_number",
    "awaiting_worker_confirmation_exit",
    "awaiting_worker_confirmation_exit_with_num"
]

def init_workers_table():
    """إنشاء جدول العمال في PostgreSQL إذا لم يكن موجود."""
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id SERIAL PRIMARY KEY,
            worker_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()

def add_worker(worker_name, phone, description):
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO workers (worker_name, phone, description) VALUES (%s, %s, %s)",
        (worker_name, phone, description)
    )
    conn.commit()
    conn.close()

def delete_worker_by_phone(phone):
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM workers WHERE phone = %s", (phone,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

def list_workers():
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT worker_name, phone, description FROM workers ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def handle_worker_service(user_id, message, user_states):
    """التعامل مع رسائل المستخدم الخاصة بخدمة العمال."""
    msg = message.strip()

    # بدء التسجيل
    if msg == "11":
        user_states[user_id] = "awaiting_worker_register"
        return "👷 أهلاً بك في خدمة العمال.\n📋 أرسل اسم العامل للتسجيل."

    # إدخال الاسم
    if user_states.get(user_id) == "awaiting_worker_register":
        user_states[user_id] = "awaiting_worker_name"
        user_states[f"{user_id}_temp_name"] = msg
        return "📞 أرسل رقم هاتف العامل."

    # إدخال الهاتف
    if user_states.get(user_id) == "awaiting_worker_name":
        user_states[user_id] = "awaiting_worker_phone"
        user_states[f"{user_id}_temp_phone"] = msg
        return "📝 أرسل وصفًا قصيرًا لمهارة العامل أو تخصصه."

    # إدخال الوصف وإضافة العامل
    if user_states.get(user_id) == "awaiting_worker_phone":
        name = user_states.pop(f"{user_id}_temp_name", "")
        phone = user_states.pop(f"{user_id}_temp_phone", "")
        description = msg
        add_worker(name, phone, description)
        user_states.pop(user_id, None)
        return f"✅ تم تسجيل العامل:\n👷 {name}\n📞 {phone}\n📝 {description}"

    # عرض قائمة العمال
    if msg == "عرض العمال":
        workers = list_workers()
        if not workers:
            return "📭 لا يوجد عمال مسجلون."
        response = "📋 *قائمة العمال المسجلين:*\n\n"
        for w_name, w_phone, w_desc in workers:
            response += f"👷 {w_name}\n📞 {w_phone}\n📝 {w_desc or '—'}\n\n"
        return response

    # حذف عامل
    if msg.startswith("حذف عامل"):
        phone_to_delete = msg.replace("حذف عامل", "").strip()
        if delete_worker_by_phone(phone_to_delete):
            return f"🗑 تم حذف العامل برقم {phone_to_delete} بنجاح."
        else:
            return "🚫 لم يتم العثور على عامل بهذا الرقم."

    return None