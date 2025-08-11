import os
import psycopg2
from psycopg2 import errors

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

PG_CONN_INFO = {
    "host": os.environ.get("PG_HOST", "dpg-d1qf0g24d50c7397llc0-a.oregon-postgres.render.com"),
    "dbname": os.environ.get("PG_DB", "remainders"),
    "user": os.environ.get("PG_USER", "remainders_user"),
    "password": os.environ.get("PG_PASSWORD", "c6G6dvxL4Y0PRZtNaZiP0mh2R5QVA0nr"),
    "port": int(os.environ.get("PG_PORT", "5432")),
}

def get_pg_connection():
    return psycopg2.connect(
        host=PG_CONN_INFO["host"],
        dbname=PG_CONN_INFO["dbname"],
        user=PG_CONN_INFO["user"],
        password=PG_CONN_INFO["password"],
        port=PG_CONN_INFO["port"],
        sslmode="require"
    )

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
    cur.execute("CREATE INDEX IF NOT EXISTS idx_workers_category ON workers (category)")
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE indexname = 'uniq_worker_phone_category'
            ) THEN
                CREATE UNIQUE INDEX uniq_worker_phone_category ON workers (phone, category);
            END IF;
        END;
        $$;
    """)
    conn.commit()
    cur.close()
    conn.close()

def resolve_category(key: str) -> str:
    key = key.strip()
    if key in WORKER_CATEGORIES:
        return WORKER_CATEGORIES[key]
    if key in WORKER_CATEGORIES.values():
        return key
    return ""

def get_worker_categories(context="browse"):
    """
    context = browse | register
    """
    header = "👷 قائمة المهن المتاحة:\n"
    body = ""
    for num, name in WORKER_CATEGORIES.items():
        body += f"{num}. {name}\n"
    footer = ""
    if context == "browse":
        footer = (
            "━━━━━━━━━━━━━━━\n"
            "➡️ أرسل رقم المهنة لعرض العمال.\n"
            "🆕 للتسجيل كعامل أرسل 55.\n"
            "🔄 للرجوع للقائمة الرئيسية أرسل 0."
        )
    else:  # register
        footer = (
            "━━━━━━━━━━━━━━━\n"
            "✅ أرسل رقم المهنة أو اسمها لاختيارها.\n"
            "❌ للإلغاء والرجوع أرسل 0."
        )
    return f"{header}{body}{footer}"

def get_workers_by_category(category_key):
    category_name = resolve_category(category_key)
    if not category_name:
        return "🚫 مهنة غير معروفة. أرسل 11 لعرض المهن."
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM workers WHERE category = %s ORDER BY id DESC", (category_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return (
            f"📭 لا يوجد عمال مسجلين في {category_name}.\n"
            "🆕 لتسجيل عامل أرسل 55\n"
            "🔄 للرجوع أرسل 11 أو 0 للقائمة الرئيسية."
        )
    msg = f"👷 قائمة {category_name}:\n"
    for name, phone in rows:
        msg += f"- {name} 📞 {phone}\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "🔄 أرسل 11 للمهن | 55 للتسجيل | 0 للقائمة الرئيسية"
    return msg

def normalize_phone(raw_phone: str) -> str:
    p = "".join(ch for ch in raw_phone if ch.isdigit() or ch == '+')
    if p.startswith("00"):
        p = "+" + p[2:]
    if p.startswith("05"):
        p = "966" + p[1:]
    return p

def save_worker(name, phone, category_key):
    category_name = resolve_category(category_key)
    if not category_name:
        return "🚫 مهنة غير صالحة."
    phone_clean = normalize_phone(phone)
    conn = get_pg_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO workers (name, phone, category) VALUES (%s, %s, %s)",
            (name.strip(), phone_clean, category_name)
        )
        conn.commit()
        return (
            f"✅ تم حفظ العامل {name.strip()} في قسم {category_name}.\n"
            "📋 لعرض نفس القسم أرسل رقمه.\n"
            "🔄 أرسل 11 للمهن أو 0 للقائمة الرئيسية."
        )
    except errors.UniqueViolation:
        conn.rollback()
        return "⚠️ هذا الرقم مسجل سابقاً في نفس القسم."
    except Exception as e:
        conn.rollback()
        return f"❗ حدث خطأ أثناء الحفظ: {e}"
    finally:
        cur.close()
        conn.close()

def handle_worker_registration(user_id, message, user_states):
    state = user_states.get(user_id)
    msg = message.strip()

    # الإلغاء العام داخل تدفق التسجيل
    if msg == "0":
        user_states.pop(user_id, None)
        return "↩️ تم الإلغاء. أرسل 11 لعرض المهن أو 0 للقائمة الرئيسية."

    if state == "awaiting_worker_category":
        category_name = resolve_category(msg)
        if category_name:
            user_states[user_id] = f"awaiting_worker_name|{category_name}"
            return f"✍️ أدخل اسم العامل المراد تسجيله في قسم {category_name}:\n❌ للإلغاء أرسل 0."
        else:
            return "🚫 مهنة غير صحيحة. أعد المحاولة أو أرسل 0 للإلغاء."

    if state and state.startswith("awaiting_worker_name"):
        _, category_name = state.split("|", 1)
        if not msg:
            return "🚫 الاسم فارغ. أعد الإدخال أو أرسل 0 للإلغاء."
        user_states[user_id] = f"awaiting_worker_phone|{category_name}|{msg}"
        return "📞 أرسل رقم العامل:\n❌ للإلغاء أرسل 0."

    if state and state.startswith("awaiting_worker_phone"):
        _, category_name, worker_name = state.split("|", 2)
        if len(msg) < 5:
            return "🚫 رقم غير صالح. أعد الإدخال أو أرسل 0 للإلغاء."
        user_states.pop(user_id, None)
        return save_worker(worker_name, msg, category_name)

    return None
