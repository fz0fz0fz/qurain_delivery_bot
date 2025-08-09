from driver_register import handle_driver_service, delete_driver
from pg_utils import generate_order_id_pg
from send_utils import send_message
from services.unified_service import handle_service
import sqlite3
import re
from search_utils import search_services_arabic
from services_data import SERVICES

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


def save_order_driver(order_number, driver_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO order_drivers (order_number, driver_id) VALUES (?, ?)", (order_number, driver_id))
    conn.commit()
    conn.close()

def get_driver_by_order(order_number):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT driver_id FROM order_drivers WHERE order_number = ? LIMIT 1", (order_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_unsent_orders_from_db(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT id, service_name, order_text, created_at FROM orders WHERE user_id = ? AND sent = 0 ORDER BY created_at ASC", (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

def mark_orders_as_sent(order_ids):
    if not order_ids:
        return
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.executemany("UPDATE orders SET sent = 1 WHERE id = ?", [(oid,) for oid in order_ids])
    conn.commit()
    conn.close()

def add_order_number_to_orders(order_number, order_ids):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.executemany("UPDATE orders SET order_number = ? WHERE id = ?", [(order_number, oid) for oid in order_ids])
    conn.commit()
    conn.close()

def get_user_id_by_order_number(order_number):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM orders WHERE order_number = ? LIMIT 1", (order_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def handle_main_menu(message):
    if message.strip() in ["0", ".", "٠", "خدمات"]:
        return main_menu_text
    return None

def handle_feedback(user_id, message, user_states):
    if message.strip() == "100":
        user_states[user_id] = "awaiting_feedback"
        return "✉️ أرسل الآن رسالتك (اقتراح أو شكوى)"
    elif user_states.get(user_id) == "awaiting_feedback":
        user_states.pop(user_id, None)
        send_message("966503813344", f"💬 شكوى من {user_id}:\n{message}")
        return "✅ تم استلام رسالتك، شكرًا لك."
    return None

def handle_view_orders(user_id, message, user_orders):
    if message.strip() == "20":
        orders = get_unsent_orders_from_db(user_id)
        if not orders:
            return "📭 لا توجد طلبات محفوظة حتى الآن."
        response = "*🗂 طلباتك المحفوظة:*\n"
        for _, service, order, created_at in orders:
            response += f"\n📌 *{service}:*\n- {order}\n🕒 {created_at}"
        response += "\n\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
        return response
    return None

def handle_finalize_order(user_id, message, user_orders):
    if message.strip() != "تم":
        return None
    orders = get_unsent_orders_from_db(user_id)
    if not orders:
        return "❗️لا توجد طلبات لإرسالها."
    order_id = generate_order_id_pg()
    summary = f"*🆔 رقم الطلب: {order_id}*\n"
    ids_to_mark = []
    for oid, service, order, created_at in orders:
        summary += f"\n📦 *{service}:*\n- {order}\n🕒 {created_at}"
        ids_to_mark.append(oid)
    add_order_number_to_orders(order_id, ids_to_mark)
    try:
        from mandoubs import mandoubs
        for m in mandoubs:
            send_message(m["id"], f"📦 طلب جديد من {user_id.replace('@c.us', '')}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")
    except ImportError:
        send_message("966503813344", f"📦 طلب جديد من {user_id.replace('@c.us', '')}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")
    for _, service, order, _ in orders:
        vendor_msg = f"*طلب جديد - {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)
    mark_orders_as_sent(ids_to_mark)
    return "✅ تم إرسال طلباتك للمناديب بنجاح!"

def handle_driver_accept_order(message, driver_id, user_states):
    match = re.match(r"قبول\s*([A-Za-z0-9]+)", message.strip())
    if match:
        order_id = match.group(1)
        user_id = get_user_id_by_order_number(order_id)
        if user_id:
            save_order_driver(order_id, driver_id)
            user_states[user_id] = "awaiting_location"
            send_message(
                user_id,
                f"🚗 تم قبول طلبك (رقم {order_id}) من قبل المندوب.\n\n"
                "📍 الرجاء الضغط على زر (📎 → الموقع → إرسال موقعك الحالي).\n"
                "❗️لا ترسل صورة أو رابط."
            )
            send_message(driver_id, f"✅ تم تسجيل قبولك للطلب رقم {order_id}. انتظر موقع العميل.")
            return "تمت معالجة قبول الطلب."
        else:
            send_message(driver_id, "🚫 لم يتم العثور على هذا الرقم.")
            return "لم يتم العثور على الطلب."
    return None

def handle_user_location(user_id, message, user_states, latitude=None, longitude=None):
    if user_states.get(user_id) == "awaiting_location":
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute(
            "SELECT order_number FROM orders WHERE user_id = ? AND sent = 1 AND order_number IS NOT NULL ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        row = c.fetchone()
        conn.close()
        order_id = row[0] if row else None
        if not order_id:
            send_message(user_id, "🚫 لم يتم العثور على رقم طلبك.")
            return "لا يوجد طلب بانتظار موقع."
        driver_id = get_driver_by_order(order_id)
        if not driver_id:
            send_message(user_id, "🚫 لم يتم العثور على المندوب المرتبط بالطلب.")
            return "لا يوجد مندوب مرتبط بالطلب."
        if latitude and longitude:
            location_url = f"https://maps.google.com/?q={latitude},{longitude}"
            send_message(driver_id, f"📍 موقع العميل للطلب رقم {order_id}: {location_url}")
            user_states.pop(user_id, None)
            send_message(user_id, "✅ تم إرسال موقعك للمندوب. شكرًا لك.")
            return "تم إرسال الموقع"
        else:
            send_message(user_id, "🚫 الرجاء إرسال الموقع عبر زر *إرسال الموقع* من واتساب وليس صورة أو نص.")
            return "يرجى إرسال الموقع الصحيح"
    return None

def format_search_results(results):
    if not results:
        return "لم يتم العثور على نتائج مطابقة.\n🔄 أرسل 0 للعودة للقائمة الرئيسية"
    msg = "*🔎 نتائج البحث:*\n\n"
    for r in results:
        if r['phone']:
            msg += f"{r['name']}\n📞 {r['phone']}\n\n"
        else:
            msg += f"{r['name']}\n\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += "🔄 أرسل 0 للعودة للقائمة الرئيسية"
    return msg

def get_service_by_keyword(keyword: str):
    """بحث جزئي وغير حساس لحالة الأحرف داخل مفاتيح SERVICES المركّبة."""
    kw = keyword.strip().lower()
    for key, value in SERVICES.items():
        for k in key.split(','):
            if kw in k.strip().lower():
                return value
    return None


def dispatch_message(
    user_id,
    message,
    user_states,
    user_orders,
    driver_id=None,
    latitude=None,
    longitude=None
):
    msg = (message or "").strip()

    # 1) التحقق من 99 لبدء الطلب داخل خدمة
    if msg in ["99", "٩٩"]:
        if not user_states.get(user_id, "").startswith("awaiting_order_"):
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."

    # 2) حالات خدمة السائقين/النقل
    driver_states = [
        "awaiting_driver_phone",
        "awaiting_driver_description",
        "awaiting_driver_delete_number",
        "awaiting_driver_confirmation_exit",
        "awaiting_driver_confirmation_exit_with_num",
        "awaiting_driver_register",
    ]

    # إظهار القائمة الرئيسية فقط إذا لم نكن داخل حالات السائقين
    if user_states.get(user_id) not in driver_states:
        response = handle_main_menu(msg)
        if response:
            return response

    # 3) عرض الطلبات المحفوظة
    response = handle_view_orders(user_id, msg, user_orders)
    if response:
        return response

    # 4) إنهاء وإرسال الطلبات
    response = handle_finalize_order(user_id, msg, user_orders)
    if response:
        return response

    # 5) استقبال الموقع من المستخدم
    response = handle_user_location(
        user_id, msg, user_states, latitude=latitude, longitude=longitude
    )
    if response:
        return response

    # 6) معالجة منطق النقل المدرسي/السائقين (14 أو كلمات تخص السائقين)
    if (
        msg == "14"
        or msg == "88"
        or msg.startswith("سائق")
        or user_states.get(user_id) in driver_states
    ):
        response = handle_driver_service(user_id, msg, user_states)
        if response:
            return response

    # 7) البحث بالكلمات المفتاحية إذا لم يكن رقم خدمة
    if not msg.isdigit():
        result = get_service_by_keyword(msg)
        if result:
            return result.get("display_msg", "تم العثور على الخدمة لكن لا توجد رسالة عرض.")

    # 8) استدعاء الخدمات الرقمية من SERVICES (باستثناء 14 لأنها للسائقين)
    if msg.isdigit() and msg in SERVICES and msg != "14":
        service_id = msg
        service_data = SERVICES[service_id]
        if "display_msg" in service_data:
            return service_data["display_msg"]
        else:
            # ملاحظة: حسب مشروعك، دالة handle_service تستقبل (user_id, message, user_states, user_orders, service_id, service_name, stores_list)
            return handle_service(
                user_id,
                msg,
                user_states,
                user_orders,
                service_id,
                service_data.get("name", ""),
                service_data.get("items", []),
            )

    # 9) لا شيء ينطبق
    return None