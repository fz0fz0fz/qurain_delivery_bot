import re
import psycopg2
from db_utils import PG_CONN_INFO

def handle_driver_service(user_id, msg, user_states):
    # استقبال "14" أو "نقل"/"مشاوير": عرض السائقين وبدء التسجيل
    if msg == "14" or msg in ["نقل", "مشاوير"]:
        user_states[user_id] = "awaiting_driver_register"
        return create_drivers_message() + "\n\n🚗 إذا أردت التسجيل كسائق أرسل: 88"

    # أي خطوة تخص التسجيل أو كان المستخدم في حالة تسجيل
    if user_states.get(user_id) == "awaiting_driver_register" or msg == "88" or msg.startswith("سائق") \
       or user_states.get(user_id) in ["awaiting_driver_name", "awaiting_driver_phone", "awaiting_driver_description"]:
        response = handle_driver_registration(user_id, msg, user_states)
        if response:
            return response

    # منطق حذف السائق برقم الجوال (يمكنك ربطه بأمر معين)
    # مثال: إذا تريد حذف سائق ترسل "حذف سائق"
    if msg in ["حذف سائق", "89", "٨٩"]:
        user_states[user_id] = "awaiting_driver_delete_number"
        return "📞 أرسل رقم السائق المراد حذفه (يمكنك كتابته بأي صيغة: 9665..., 05..., 5...):"

    # استقبال رقم السائق للحذف
    if user_states.get(user_id) == "awaiting_driver_delete_number":
        result = handle_driver_number_deletion(msg)
        user_states.pop(user_id, None)
        return result

    # حذف السائق بناء على معرف المستخدم
    if msg in ["حذف بياناتي كسائق", "حذفني"]:
        return handle_driver_deletion(user_id)

    return None

def handle_driver_registration(user_id: str, message: str, user_states: dict) -> str or None:
    """
    كل حالات التسجيل للسائقين هنا فقط.
    الاسم -> الرقم -> وصف الخدمة -> تسجيل سريع برسالة واحدة.
    """
    # بدء التسجيل
    if message.strip() in ["سائق", "سائق نقل", "سائق مشاوير", "88"]:
        user_states[user_id] = "awaiting_driver_name"
        return "🚗 أرسل اسمك للتسجيل كسائق:"

    # الخطوة الثانية: الاسم
    if user_states.get(user_id) == "awaiting_driver_name":
        user_states[f"{user_id}_driver_name"] = message.strip()
        user_states[user_id] = "awaiting_driver_phone"
        return "📞 أرسل رقم جوالك (مثال: 9665xxxxxxxx):"

    # الخطوة الثالثة: الرقم
    if user_states.get(user_id) == "awaiting_driver_phone":
        name = user_states.get(f"{user_id}_driver_name", "")
        phone_input = message.strip()
        phone_real = extract_phone_from_user_id(user_id)
        phone_input_norm = normalize_phone(phone_input)
        if phone_input_norm != phone_real:
            user_states.pop(user_id, None)
            user_states.pop(f"{user_id}_driver_name", None)
            return f"🚫 يجب أن تسجل برقم جوالك المرتبط بالواتساب: {phone_real}"
        if driver_exists(phone_real):
            user_states.pop(user_id, None)
            user_states.pop(f"{user_id}_driver_name", None)
            return "✅ أنت مسجل مسبقاً كسائق لدينا."
        user_states[f"{user_id}_driver_phone"] = phone_real
        user_states[user_id] = "awaiting_driver_description"
        return (
            "📝 أرسل وصف خدمتك (مثال: نقل من القرين لمدرسة (كذا) أو لكلية (كذا)):"
        )

    # الخطوة الرابعة: وصف الخدمة
    if user_states.get(user_id) == "awaiting_driver_description":
        name = user_states.get(f"{user_id}_driver_name", "")
        phone = user_states.get(f"{user_id}_driver_phone", "")
        desc = message.strip()
        add_driver(name, phone, user_id, desc)
        user_states.pop(user_id, None)
        user_states.pop(f"{user_id}_driver_name", None)
        user_states.pop(f"{user_id}_driver_phone", None)
        return (
            f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name}\nالرقم: {phone}\nالوصف: {desc}"
        )

    # التسجيل السريع (سائق - اسم - رقم)
    match = re.match(
        r"سائق(?: نقل| مشاوير)?\s*[-:،]?\s*([^\d\-:،]+)\s*[-:،]\s*([0-9+]+)",
        message.strip()
    )
    if match:
        name, phone_in_msg = match.groups()
        phone_from_sender = extract_phone_from_user_id(user_id)
        phone_in_msg_norm = normalize_phone(phone_in_msg)
        if phone_in_msg_norm != phone_from_sender:
            return "❌ رقم الهاتف في الرسالة لا يطابق رقمك في واتساب. الرجاء التأكد من إرسال رقمك الصحيح."
        if driver_exists(phone_from_sender):
            return "✅ أنت مسجل مسبقًا كسائق لدينا."
        # لا يوجد وصف في التسجيل السريع
        add_driver(name.strip(), phone_from_sender, user_id, "")
        return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name.strip()}\nالرقم: {phone_from_sender}"

    return None

def normalize_phone(phone: str) -> str:
    """
    تحويل رقم الجوال إلى صيغة 9665xxxxxxxx
    يدعم: 05xxxxxxxx, +9665xxxxxxxx, 9665xxxxxxxx, 5xxxxxxxx, 009665xxxxxxxx
    """
    phone = str(phone).strip()
    phone = phone.replace(" ", "").replace("-", "").replace("_", "")
    if phone.startswith("00"):
        phone = "966" + phone[2:]
    elif phone.startswith("+966"):
        phone = "966" + phone[4:]
    elif phone.startswith("0"):
        phone = "966" + phone[1:]
    elif phone.startswith("5") and len(phone) == 9:
        phone = "966" + phone
    return phone

def driver_exists(phone: str) -> bool:
    """يتحقق هل السائق موجود مسبقًا برقم الجوال."""
    phone = normalize_phone(phone)
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM drivers WHERE phone = %s", (phone,))
                return cur.fetchone() is not None
    except Exception as e:
        print(f"Error in driver_exists: {e}")
        return False

def add_driver(name: str, phone: str, user_id: str, description: str = "") -> None:
    """إضافة سائق جديد إذا لم يكن موجود."""
    phone = normalize_phone(phone)
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO drivers (name, phone, user_id, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (phone) DO NOTHING
                """, (name, phone, user_id, description))
                conn.commit()
    except Exception as e:
        print(f"Error in add_driver: {e}")

def handle_driver_number_deletion(phone_input: str) -> str:
    """
    حذف سائق بناءً على رقم الجوال بأي صيغة.
    يبحث عن الرقم في جميع الصيغ الشائعة.
    """
    candidates = set()
    phone = str(phone_input).strip().replace(" ", "").replace("-", "").replace("_", "")

    if phone.startswith("00"):
        phone_966 = "966" + phone[2:]
        candidates.add(phone_966)
        candidates.add(phone_966[3:])  # بدون 966
    elif phone.startswith("+966"):
        phone_966 = "966" + phone[4:]
        candidates.add(phone_966)
        candidates.add(phone_966[3:])
    elif phone.startswith("966"):
        candidates.add(phone)
        candidates.add(phone[3:])
        if len(phone) >= 12 and phone[3] == "0":
            candidates.add("0" + phone[4:])
    elif phone.startswith("0"):
        candidates.add("966" + phone[1:])
        candidates.add(phone)
        if len(phone) >= 10 and phone[1] == "5":
            candidates.add(phone[1:])  # 5xxxxxxxx
    elif phone.startswith("5") and len(phone) == 9:
        candidates.add("966" + phone)
        candidates.add("05" + phone)
        candidates.add(phone)
    else:
        candidates.add(phone)
        if phone.startswith("5"):
            candidates.add("966" + phone)
            candidates.add("05" + phone)
        elif phone.startswith("05"):
            candidates.add("966" + phone) 
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                for candidate in candidates:
                    cur.execute("SELECT id FROM drivers WHERE phone = %s", (candidate,))
                    row = cur.fetchone()
                    if not row and len(candidate) >= 8:
                        cur.execute("SELECT id FROM drivers WHERE phone LIKE %s", ('%' + candidate[-8:],))
                        row = cur.fetchone()
                    if row:
                        driver_id = row[0]
                        cur.execute("DELETE FROM drivers WHERE id = %s", (driver_id,))
                        conn.commit()
                        found = True
                        break
    except Exception as e:
        print(f"Error in handle_driver_number_deletion: {e}")
        return "🚫 حدث خطأ أثناء حذف السائق، حاول مرة أخرى لاحقًا."

    if found:
        return "✅ تم حذف السائق بنجاح."
    else:
        return "🚫 لم يتم العثور على السائق بهذا الرقم."

def handle_driver_deletion(user_id: str) -> str:
    """حذف السائق بناء على معرف المستخدم."""
    _, msg = delete_driver_by_user_id(user_id)
    return msg

def delete_driver_by_user_id(user_id: str) -> (bool, str):
    """يحذف السائق بناءً على رقم جواله من معرف واتساب."""
    phone = extract_phone_from_user_id(user_id)
    if not driver_exists(phone):
        return False, "🚫 لم يتم العثور على بياناتك كسائق لدينا."
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM drivers WHERE phone = %s", (phone,))
                deleted = cur.rowcount
                conn.commit()
                if deleted:
                    return True, "✅ تم حذفك من قائمة السائقين بنجاح."
                else:
                    return False, "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."
    except Exception as e:
        print(f"Error in delete_driver_by_user_id: {e}")
        return False, "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."

def get_all_drivers() -> list:
    """إرجاع قائمة كل السائقين (اسم - رقم - وصف)."""
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, phone, description FROM drivers ORDER BY created_at DESC")
                drivers = cur.fetchall()
                return [(name, normalize_phone(phone), desc or "") for name, phone, desc in drivers]
    except Exception as e:
        print(f"Error in get_all_drivers: {e}")
        return []

def extract_phone_from_user_id(user_id: str) -> str:
    """استخراج رقم الجوال من معرف واتساب."""
    return normalize_phone(user_id.split("@")[0] if "@c.us" in user_id else user_id)

def create_drivers_message() -> str:
    """عرض رسالة بكل السائقين المسجلين للنقل المدرسي."""
    drivers = get_all_drivers()
    if not drivers:
        drivers_list = "لا يوجد سائقين مسجلين حالياً."
    else:
        drivers_list = "\n".join([
            f"{name} - {phone}\n{desc}" if desc else f"{name} - {phone}"
            for name, phone, desc in drivers
        ])
    msg = (
        "🚕 *خدمة النقل المدرسي والمشاوير*\n"
        "إذا أردت التسجيل كسائق في خدمة النقل، أرسل: *سائق - اسمك - رقمك*\n"
        "مثال: سائق - أحمد - 966512345678\n"
        "━━━━━━━━━━━━━━━\n"
        "*قائمة السائقين المتاحين:*\n"
        f"{drivers_list}\n"
        "━━━━━━━━━━━━━━━"
    )
    return msg