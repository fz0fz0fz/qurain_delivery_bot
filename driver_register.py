import re
import psycopg2
from db_utils import PG_CONN_INFO

def handle_driver_service(user_id, msg, user_states):
    # استقبال "14" أو "نقل"/"مشاوير": عرض السائقين وبدء التسجيل
    if msg == "14" or msg in ["نقل", "مشاوير"]:
        user_states[user_id] = "awaiting_driver_register"
        return create_drivers_message()

    # أي خطوة تخص التسجيل أو كان المستخدم في حالة تسجيل
    if user_states.get(user_id) == "awaiting_driver_register" or msg == "88" or msg.strip() == "تسجيل" \
       or user_states.get(user_id) in ["awaiting_driver_name", "awaiting_driver_phone", "awaiting_driver_description"]:
        response = handle_driver_registration(user_id, msg, user_states)
        if response:
            return response

    # منطق حذف السائق برقم الجوال أو المعرف الشخصي
    if msg in ["حذف سائق", "77", "٧٧"]:
        user_states[user_id] = "awaiting_driver_delete_number"
        return "📞 أرسل رقم السائق المراد حذفه (يمكنك كتابته بأي صيغة: 9665..., 05..., 5...):"

    if user_states.get(user_id) == "awaiting_driver_delete_number":
        result = handle_driver_number_deletion(msg, user_id)
        user_states.pop(user_id, None)
        return result

    if msg in ["احذف", "حذف", "ازاله", "إزالة"]:
        return delete_driver(user_id)

    return None

def handle_driver_registration(user_id: str, message: str, user_states: dict) -> str or None:
    """
    كل حالات التسجيل للسائقين هنا فقط.
    الاسم -> الرقم -> وصف الخدمة -> تسجيل سريع برسالة واحدة.
    """
    # بدء التسجيل
    if message.strip() in ["تسجيل", "88"]:
        user_states[user_id] = "awaiting_driver_name"
        return "🚗 أرسل اسمك فقط للتسجيل كسائق:"

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
        return "📝 أرسل وصف خدمتك (مثال: نقل من القرين لمدرسة (كذا) أو لكلية (كذا)):"

    # الخطوة الرابعة: وصف الخدمة
    if user_states.get(user_id) == "awaiting_driver_description":
        name = user_states.get(f"{user_id}_driver_name", "")
        phone = user_states.get(f"{user_id}_driver_phone", "")
        desc = message.strip()
        add_driver(name, phone, user_id, desc)
        user_states.pop(user_id, None)
        user_states.pop(f"{user_id}_driver_name", None)
        user_states.pop(f"{user_id}_driver_phone", None)
        return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name}\nالرقم: {phone}\nالوصف: {desc}"

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

def delete_driver(user_id: str, phone_input: str = None) -> str:
    """
    حذف سائق. إذا لم يُعطَ رقم، يحذف بيانات المستخدم نفسه.
    إذا أُعطي رقم، يجب أن يكون مطابق لرقم المستخدم الفعلي (لا يمكن حذف سائق آخر).
    """
    phone_real = extract_phone_from_user_id(user_id)
    if phone_input is None:
        if not driver_exists(phone_real):
            return "🚫 لم يتم العثور على بياناتك كسائق لدينا."
        try:
            with psycopg2.connect(**PG_CONN_INFO) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM drivers WHERE phone = %s", (phone_real,))
                    deleted = cur.rowcount
                    conn.commit()
                    if deleted:
                        return "✅ تم حذفك من قائمة السائقين بنجاح."
                    else:
                        return "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."
        except Exception as e:
            print(f"Error in delete_driver (self): {e}")
            return "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."
    else:
        phone_input_norm = normalize_phone(phone_input)
        if phone_input_norm != phone_real:
            return "🚫 لا يمكنك حذف إلا بياناتك الشخصية فقط، يجب أن يكون الرقم مطابق لرقمك في واتساب."
        if not driver_exists(phone_real):
            return "🚫 لم يتم العثور على بياناتك كسائق لدينا."
        try:
            with psycopg2.connect(**PG_CONN_INFO) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM drivers WHERE phone = %s", (phone_real,))
                    deleted = cur.rowcount
                    conn.commit()
                    if deleted:
                        return "✅ تم حذف بياناتك كسائق بنجاح."
                    else:
                        return "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."
        except Exception as e:
            print(f"Error in delete_driver (by phone): {e}")
            return "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."

def handle_driver_number_deletion(phone_input, user_id):
    """
    منطق استقبال رقم السائق للحذف، يستدعي منطق الحذف الموحد.
    """
    return delete_driver(user_id, phone_input)

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

def format_drivers_list(drivers):
    output = (
        "🚕✨ *خدمة النقل المدرسي والمشاوير* ✨🚕\n\n"
        "✳️ للتسجيل كسائق فقط أرسل كلمة *تسجيل* أو رقم *88*\n"
        "🔴 للحذف أرسل كلمة *حذف* أو رقم *77*\n"
        "━━━━━━━━━━━━━━━\n"
        "*🚗 قائمة السائقين المتاحين:*\n"
    )
    if not drivers:
        output += "لا يوجد سائقين متاحين حالياً.\n"
    else:
        for idx, driver in enumerate(drivers, 1):
            if isinstance(driver, tuple):
                name, phone, desc = driver
            else:
                name = driver.get('name', '')
                phone = driver.get('phone', '')
                desc = driver.get('desc', '')
            output += (
                f"• {name} - {phone}\n"
                f"   {desc}\n"
                "-------------------------\n"
            )
    output += (
        "━━━━━━━━━━━━━━━\n"
        "✳️ للتسجيل كسائق فقط أرسل كلمة *تسجيل* أو رقم *88*\n"
        "🔴 للحذف أرسل كلمة *حذف* أو رقم *77*\n"
        "━━━━━━━━━━━━━━━"
    )
    return output

def create_drivers_message() -> str:
    """عرض رسالة بكل السائقين المسجلين للنقل المدرسي."""
    drivers = get_all_drivers()
    msg = format_drivers_list(drivers)
    return msg