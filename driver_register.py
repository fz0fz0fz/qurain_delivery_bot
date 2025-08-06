import re
import psycopg2
from db_utils import PG_CONN_INFO

def normalize_phone(phone: str) -> str:
    """Normalize phone numbers to the 9665xxxxxxxx format."""
    phone = str(phone).strip()
    phone = phone.replace(" ", "").replace("-", "").replace("_", "")
    if phone.startswith("00"):
        phone = "966" + phone[2:]
    elif phone.startswith("+966"):
        phone = "966" + phone[4:]
    elif phone.startswith("0"):
        phone = "966" + phone[1:]
    return phone

def driver_exists(phone: str) -> bool:
    """Check if a driver with this phone exists."""
    phone = normalize_phone(phone)
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT id FROM drivers WHERE phone = %s", (phone,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def add_driver(name: str, phone: str, user_id: str) -> None:
    """Add a new driver, if not exists."""
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

def delete_driver_by_user_id(user_id: str) -> (bool, str):
    """Delete a driver by user_id, returns (success, message)."""
    phone = extract_phone_from_user_id(user_id)
    if not driver_exists(phone):
        return False, "🚫 لم يتم العثور على بياناتك كسائق لدينا."
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("DELETE FROM drivers WHERE phone = %s", (phone,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        return True, "✅ تم حذفك من قائمة السائقين بنجاح."
    else:
        return False, "🚫 حدث خطأ أثناء حذف بياناتك، حاول مرة أخرى لاحقًا."

def get_all_drivers() -> list:
    """Return a list of all drivers as (name, phone) tuples."""
    conn = psycopg2.connect(**PG_CONN_INFO)
    cur = conn.cursor()
    cur.execute("SELECT name, phone FROM drivers ORDER BY created_at DESC")
    drivers = cur.fetchall()
    cur.close()
    conn.close()
    return drivers

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
    """
    # Step 1: Start registration
    if message.strip() in ["سائق", "سائق نقل", "سائق مشاوير"]:
        user_states[user_id] = "awaiting_driver_name"
        return "🚗 أرسل اسمك للتسجيل كسائق:"
    # Step 2: Receive Name
    if user_states.get(user_id) == "awaiting_driver_name":
        user_states[f"{user_id}_driver_name"] = message.strip()
        user_states[user_id] = "awaiting_driver_phone"
        return "📞 أرسل رقم جوالك (مثال: 9665xxxxxxxx):"
    # Step 3: Receive Phone
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
        add_driver(name, phone_real, user_id)
        user_states.pop(user_id, None)
        user_states.pop(f"{user_id}_driver_name", None)
        return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name}\nالرقم: {phone_real}"
    # تسجيل سريع برسالة واحدة
    match = re.match(r"سائق(?: نقل| مشاوير)?\s*[-:،]?\s*([^\d\-]+)\s*[-:،]\s*(\d+)", message)
    if match:
        name, phone_in_msg = match.groups()
        phone_from_sender = extract_phone_from_user_id(user_id)
        phone_in_msg_norm = normalize_phone(phone_in_msg)
        if phone_in_msg_norm != phone_from_sender:
            return "❌ رقم الهاتف في الرسالة لا يطابق رقمك في واتساب. الرجاء التأكد من إرسال رقمك الصحيح."
        if driver_exists(phone_from_sender):
            return "✅ أنت مسجل مسبقًا كسائق لدينا."
        add_driver(name.strip(), phone_from_sender, user_id)
        return f"✅ تم تسجيلك بنجاح كسائق.\nالاسم: {name.strip()}\nالرقم: {phone_from_sender}"
    return None

def handle_driver_deletion(user_id: str) -> str:
    """Handles the driver deletion command, returns a response message."""
    _, msg = delete_driver_by_user_id(user_id)
    return msg