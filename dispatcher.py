from pg_utils import generate_order_id_pg
from send_utils import send_message
from services.unified_service import handle_service
import sqlite3
import re

# تعريف قاموس الخدمات الموحد
allowed_service_ids = {
    "1": "حكومي",
    "2": "صيدلية",
    "3": "بقالة",
    "4": "خضار",
    "5": "رحلات",
    "6": "حلا",
    "7": "أسر منتجة",
    "8": "مطاعم",
    "9": "قرطاسية",
    "10": "محلات",
    "11": "شالية",
    "12": "وايت",
    "13": "شيول",
    "14": "دفان",
    "15": "مواد بناء وعوازل",
    "16": "عمال",
    "17": "محلات مهنية",
    "18": "ذبائح وملاحم",
    "19": "نقل مدرسي ومشاوير",
    "20": "طلباتك"
}

# نص القائمة الرئيسية الموحد
main_menu_text = (
    "*📋 خدمات القرين:*\n"
    "1️⃣ حكومي\n"
    "2️⃣ صيدلية 💊\n"
    "3️⃣ بقالة 🥤\n"
    "4️⃣ خضار 🥬\n"
    "5️⃣ رحلات ⛺️\n"
    "6️⃣ حلا 🍮\n"
    "7️⃣ أسر منتجة 🥧\n"
    "8️⃣ مطاعم 🍔\n"
    "9️⃣ قرطاسية 📗\n"
    "🔟 محلات 🏪\n"
    "11. شالية 🏖\n"
    "12. وايت 🚛\n"
    "13. شيول 🚜\n"
    "14. دفان 🏗\n"
    "15. مواد بناء وعوازل 🧱\n"
    "16. عمال 👷\n"
    "17. محلات مهنية 🔨\n"
    "18. ذبائح وملاحم 🥩\n"
    "19. نقل مدرسي ومشاوير 🚍\n"
    "20. طلباتك 🧾\n\n"
    "✉️ لاقتراح أو شكوى أرسل: 100"
)

# بقية الكود كما هو في ملفك السابق
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

def dispatch_message(user_id, message, user_states, user_orders, driver_id=None, latitude=None, longitude=None):
    if message.strip() in ["99", "٩٩"]:
        if not user_states.get(user_id, "").startswith("awaiting_order_"):
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."
    response = handle_main_menu(message)
    if response: return response
    response = handle_feedback(user_id, message, user_states)
    if response: return response
    response = handle_view_orders(user_id, message, user_orders)
    if response: return response
    response = handle_finalize_order(user_id, message, user_orders)
    if response: return response
    if driver_id:
        response = handle_driver_accept_order(message, driver_id, user_states)
        if response: return response
    response = handle_user_location(user_id, message, user_states, latitude=latitude, longitude=longitude)
    if response: return response
    for service_id, service_info in {
        "2": {"name": "الصيدلية", "stores": ["صيدلية الدواء", "صيدلية النهدي"]},
        "3": {"name": "البقالة", "stores": ["بقالة التميمي", "بقالة الخير"]},
        "4": {"name": "الخضار", "stores": ["خضار الطازج", "سوق المزارعين"]},
    }.items():
        response = handle_service(
            user_id,
            message,
            user_states,
            user_orders,
            service_id,
            service_info["name"],
            service_info["stores"],
            allowed_service_ids,
            main_menu_text
        )
        if response:
            return response
    return None