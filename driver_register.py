import re
import psycopg2
from db_utils import PG_CONN_INFO

def normalize_phone(phone: str) -> str:
    """
    Normalize phone numbers to 9665xxxxxxxx format.
    Supports: 05xxxxxxxx, +9665xxxxxxxx, 9665xxxxxxxx, 5xxxxxxxx, 009665xxxxxxxx
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
    """Check if a driver with this phone exists."""
    phone = normalize_phone(phone)
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM drivers WHERE phone = %s", (phone,))
                return cur.fetchone() is not None
    except Exception as e:
        print(f"Error in driver_exists: {e}")
        return False

def handle_driver_number_deletion(phone_input: str) -> str:
    """
    يحذف سائق بناءً على رقم يُعطى بأي صيغة (دولي أو محلي).
    يبحث عن الرقم في جميع الصيغ الشائعة، ويطبع قائمة السائقين في اللوق.
    """
    # --- اطبع كل الأرقام الموجودة في قاعدة البيانات ---
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, phone FROM drivers ORDER BY id DESC")
                rows = cur.fetchall()
                print("=== قائمة السائقين في قاعدة البيانات ===")
                for row in rows:
                    print(f"id={row[0]}, name={row[1]}, phone={row[2]}")
                print("=== نهاية القائمة ===")
    except Exception as e:
        print(f"Error printing drivers: {e}")
    # --- نهاية الطباعة ---

    candidates = set()
    phone = str(phone_input).strip().replace(" ", "").replace("-", "").replace("_", "")

    # أضف كل الصيغ الممكنة للبحث
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
        # fallback: جرّب الرقم نفسه + بدون أول رقم + مع 966
        candidates.add(phone)
        if phone.startswith("5"):
            candidates.add("966" + phone)
            candidates.add("05" + phone)
        elif phone.startswith("05"):
            candidates.add("966" + phone[1:])

    found = False
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                for candidate in candidates:
                    print(f"Trying candidate: {candidate}")  # تطبع كل صيغة يجربها الكود
                    cur.execute("SELECT id FROM drivers WHERE phone = %s", (candidate,))
                    row = cur.fetchone()
                    if not row and len(candidate) >= 8:
                        # fallback: بحث جزئي (آخر 8 أرقام على الأقل)
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

def add_driver(name: str, phone: str, user_id: str, description: str = "") -> None:
    """Add a new driver, if not exists."""
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

def delete_driver_by_user_id(user_id: str) -> (bool, str):
    """Delete a driver by user_id, returns (success, message)."""
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
    """Return a list of all drivers as (name, phone) tuples, phones normalized."""
    try:
        with psycopg2.connect(**PG_CONN_INFO) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, phone FROM drivers ORDER BY created_at DESC")
                drivers = cur.fetchall()
                # Normalize all phones before returning
                return [(name, normalize_phone(phone)) for name, phone in drivers]
    except Exception as e:
        print(f"Error in get_all_drivers: {e}")
        return []

def extract_phone_from_user_id(user_id: str) -> str:
    """Helper to extract phone from WhatsApp user_id."""
    return normalize_phone(user_id.split("@")[0] if "@c.us" in user_id else user_id)

def create_drivers_message() -> str:
    """Return a message with all registered drivers for school transport."""
    drivers = get_all_drivers()
    if not drivers:
        drivers_list = "لا يوجد سائقين مسجلين حالياً."
    else:
        drivers_list = "\n".join([f"{name} - {phone}" for name, phone in drivers])
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

def handle_driver_registration(user_id: str, message: str, user_states: dict) -> str or None:
    """
    Handles the driver registration flow.
    Usage: message from user, user_states dict, returns response or None.
    الآن التسجيل ثلاث خطوات: الاسم -> الرقم -> وصف الخدمة
    """
    # بدء التسجيل
    if message.strip() in ["سائق", "سائق نقل", "سائق مشاوير"]:
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
    # تسجيل سريع برسالة واحدة (لن ندعم الوصف هنا، إلا إذا أردت)
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

def handle_driver_deletion(user_id: str) -> str:
    """Handles the driver deletion command, returns a response message."""
    _, msg = delete_driver_by_user_id(user_id)
    return msg
