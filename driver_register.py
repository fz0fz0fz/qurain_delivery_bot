import re
import psycopg2
from db_utils import PG_CONN_INFO

# قائمة الخدمات حسب الأرقام
allowed_service_ids = {
    "1": "حكومي",
    "2": "صيدلية",
    "3": "بقالة",
    "4": "خضار",
    "5": "حلا وأسر منتجة",
    "6": "مطاعم",
    "7": "محلات",
    "8": "شالية",
    "9": "وايت",
    "10": "شيول ومواد بناء",
    "11": "عمال",
    "12": "محلات مهنية",
    "13": "ذبائح وملاحم",
    "14": "نقل مدرسي ومشاوير",
    "15": "تأجير"
}

main_menu_text = (
    "📖 *دليلك لخدمات القرين*\n"
    "👋 أهلاً وسهلاً بك! اختر رقم الخدمة من القائمة أدناه، أو أرسل `0` للعودة للقائمة الرئيسية في أي وقت.\n\n"
    "*📋 الخدمات المتاحة:*\n\n"
    "1. حكومي\n"
    "2. صيدلية 💊\n"
    "3. بقالة 🥤\n"
    "4. خضار 🥬\n"
    "5. حلا وأسر منتجة 🍮\n"
    "6. مطاعم 🍔\n"
    "7. محلات 🏪\n"
    "8. شالية 🏖\n"
    "9. وايت 🚛\n"
    "10. شيول ومواد بناء 🧱\n"
    "11. عمال 👷\n"
    "12. محلات مهنية 🔨\n"
    "13. ذبائح وملاحم 🥩\n"
    "14. نقل مدرسي ومشاوير 🚍\n"
    "15. تأجير 📦\n"
    "━━━━━━━━━━━━━━━\n"
    "✉️ *للاقتراحات:* أرسل `100`\n"
    "━━━━━━━━━━━━━━━"
)

def service_handler(user_id, requested_num, user_states):
    # دعم الأرقام العربية
    num_map = {
        "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5",
        "٦": "6", "٧": "7", "٨": "8", "٩": "9", "١٠": "10",
        "١١": "11", "١٢": "12", "١٣": "13", "١٤": "14", "١٥": "15"
    }
    num = num_map.get(requested_num.strip(), requested_num.strip())
    if num == "0":
        return main_menu_text
    if num in allowed_service_ids:
        service_name = allowed_service_ids[num]
        return f"✅ لقد اخترت خدمة رقم [{num}] وهي: *{service_name}*.\n\nأرسل أي رقم آخر للانتقال لخدمة أخرى أو أرسل `0` للقائمة الرئيسية."
    else:
        return "🚫 الرقم غير صحيح أو الخدمة غير موجودة.\nيرجى اختيار رقم من القائمة أو أرسل `0` للقائمة الرئيسية."

def handle_driver_service(user_id, msg, user_states):
    # كلمات وأرقام الخدمات التي تعني رغبة بالخروج من التسجيل/الحذف
    exit_keywords = [
        "نقل", "صيدلية", "مطعم", "بقالة", "خضار", "حلا", "محلات", "شالية", "وايت", "عمال",
        "مهنية", "ذبائح", "نقل مدرسي", "تأجير", "١٤", "14", "٢", "2", "3", "4", "5", "77", "٧٧", "88", "٨٨"
    ]
    numbers_ar = [str(i) for i in range(1, 16)]
    numbers_arabic = ["١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩", "١٠", "١١", "١٢", "١٣", "١٤", "١٥"]
    exit_keywords.extend(numbers_ar)
    exit_keywords.extend(numbers_arabic)

    # منطق الخروج الذكي أثناء التسجيل أو الحذف
    if user_states.get(user_id) in [
        "awaiting_driver_name", "awaiting_driver_phone", "awaiting_driver_description", "awaiting_driver_delete_number"
    ]:
        if msg.strip() in exit_keywords:
            # حفظ الحالة السابقة قبل التأكيد
            user_states[f"{user_id}_prev_state"] = user_states.get(user_id)
            # إذا كانت رقم خدمة من 1 إلى 15 احفظ الرقم المطلوب
            if msg.strip() in numbers_ar + numbers_arabic:
                user_states[user_id] = "awaiting_driver_confirmation_exit_with_num"
                user_states[f"{user_id}_requested_num"] = msg.strip()
                return f"⚠️ أنت الآن في عملية التسجيل أو الحذف.\nهل تريد الخروج والانتقال إلى الخدمة رقم [{msg.strip()}]؟ (أرسل نعم للخروج أو لا للمتابعة)"
            else:
                user_states[user_id] = "awaiting_driver_confirmation_exit"
                return "⚠️ أنت الآن في عملية التسجيل أو الحذف. هل تريد الخروج؟ (أرسل نعم للخروج أو لا للمتابعة)"

    # منطق تأكيد الخروج مع رقم خدمة
    if user_states.get(user_id) == "awaiting_driver_confirmation_exit_with_num":
        if msg.strip() == "نعم":
            requested_num = user_states.pop(f"{user_id}_requested_num", None)
            user_states.pop(user_id, None)
            user_states.pop(f"{user_id}_prev_state", None)
            return service_handler(user_id, requested_num, user_states)
        elif msg.strip() == "لا":
            prev_state = user_states.pop(f"{user_id}_prev_state", "awaiting_driver_register")
            user_states[user_id] = prev_state
            if prev_state == "awaiting_driver_name":
                return "🚗 أرسل اسمك فقط للتسجيل كسائق:"
            elif prev_state == "awaiting_driver_phone":
                return "📞 أرسل رقم جوالك (مثال: 9665xxxxxxxx):"
            elif prev_state == "awaiting_driver_description":
                return "📝 أرسل وصف خدمتك (مثال: نقل من القرين لمدرسة (كذا) أو لكلية (كذا)):"
            elif prev_state == "awaiting_driver_delete_number":
                return "📞 أرسل رقم السائق المراد حذفه (يمكنك كتابته بأي صيغة: 9665..., 05..., 5...):"
            else:
                return "🚗 الرجاء متابعة عملية التسجيل أو الحذف."

    # منطق تأكيد الخروج بدون رقم خدمة
    if user_states.get(user_id) == "awaiting_driver_confirmation_exit":
        if msg.strip() == "نعم":
            user_states.pop(user_id, None)
            user_states.pop(f"{user_id}_prev_state", None)
            return "✅ تم الخروج من العملية. يمكنك اختيار خدمة أخرى."
        elif msg.strip() == "لا":
            prev_state = user_states.pop(f"{user_id}_prev_state", "awaiting_driver_register")
            user_states[user_id] = prev_state
            if prev_state == "awaiting_driver_name":
                return "🚗 أرسل اسمك فقط للتسجيل كسائق:"
            elif prev_state == "awaiting_driver_phone":
                return "📞 أرسل رقم جوالك (مثال: 9665xxxxxxxx):"
            elif prev_state == "awaiting_driver_description":
                return "📝 أرسل وصف خدمتك (مثال: نقل من القرين لمدرسة (كذا) أو لكلية (كذا)):"
            elif prev_state == "awaiting_driver_delete_number":
                return "📞 أرسل رقم السائق المراد حذفه (يمكنك كتابته بأي صيغة: 9665..., 05..., 5...):"
            else:
                return "🚗 الرجاء متابعة عملية التسجيل أو الحذف."

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