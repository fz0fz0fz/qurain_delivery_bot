# workers_register.py
import psycopg2
from send_utils import send_message

# قائمة المهن
WORKER_CATEGORIES = {
    "1": "سباكين",
    "2": "كهربائيين",
    "3": "نجارين",
    "4": "حدادين",
    "5": "دهانين",
    "6": "بلاط",
    "7": "تنظيف",
    "8": "أخرى"
}

# الاتصال بقاعدة PostgreSQL
def get_pg_connection():
    return psycopg2.connect(
        dbname="YOUR_DB",
        user="YOUR_USER",
        password="YOUR_PASSWORD",
        host="YOUR_HOST",
        port="5432"
    )

# إنشاء جدول العمال إذا لم يكن موجود
def init_workers_table():
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# عرض قائمة المهن
def get_worker_categories():
    msg = "*👷 قائمة المهن المتاحة:*\n"
    for num, name in WORKER_CATEGORIES.items():
        msg += f"{num}. {name}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "📌 للتسجيل كعامل أرسل `55`"
    return msg

# عرض عمال مهنة معينة
def get_workers_by_category(category_key):
    category_name = WORKER_CATEGORIES.get(category_key) or category_key
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM workers WHERE category = %s", (category_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return f"📭 لا يوجد عمال مسجلين في *{category_name}* حتى الآن."
    
    msg = f"*👷 قائمة {category_name}:*\n"
    for name, phone in rows:
        msg += f"- {name} 📞 {phone}\n"
    return msg

# حفظ عامل جديد
def save_worker(name, phone, category_key):
    category_name = WORKER_CATEGORIES.get(category_key) or category_key
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO workers (name, phone, category) VALUES (%s, %s, %s)",
                (name, phone, category_name))
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ تم حفظ العامل *{name}* في قسم *{category_name}* بنجاح."

# معالجة تسجيل عامل
def handle_worker_registration(user_id, message, user_states):
    state = user_states.get(user_id)

    # اختيار المهنة
    if state == "awaiting_worker_category":
        category_key = message.strip()
        if category_key in WORKER_CATEGORIES or category_key in WORKER_CATEGORIES.values():
            user_states[user_id] = f"awaiting_worker_name|{category_key}"
            return "✍️ أدخل اسم العامل:"
        else:
            return "🚫 مهنة غير صحيحة، حاول مرة أخرى."

    # إدخال اسم العامل
    elif state and state.startswith("awaiting_worker_name"):
        _, category_key = state.split("|")
        user_states[user_id] = f"awaiting_worker_phone|{category_key}|{message.strip()}"
        return "📞 أدخل رقم العامل:"

    # إدخال رقم العامل
    elif state and state.startswith("awaiting_worker_phone"):
        _, category_key, worker_name = state.split("|", 2)
        worker_phone = message.strip()
        user_states.pop(user_id, None)
        return save_worker(worker_name, worker_phone, category_key)

    return None