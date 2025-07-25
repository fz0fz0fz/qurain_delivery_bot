from send_utils import send_message, generate_order_id
from services.unified_service import handle_service
import sqlite3

order_to_user = {}     # order_id -> user_id
order_to_driver = {}   # order_id -> driver_id

def handle_main_menu(message):
    if message.strip() in ["0", ".", "٠", "خدمات"]:
        return (
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

def get_orders_from_db(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT service_name, order_text, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

def handle_view_orders(user_id, message, user_orders):
    if message.strip() == "20":
        orders = get_orders_from_db(user_id)
        if not orders:
            return "📭 لا توجد طلبات محفوظة حتى الآن."
        response = "*🗂 طلباتك المحفوظة:*\n"
        for service, order, created_at in orders:
            response += f"\n📌 *{service}:*\n- {order}\n🕒 {created_at}"
        response += "\n\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
        return response
    return None

# باقي الكود كما هو

def handle_finalize_order(user_id, message, user_orders):
    if message.strip() != "تم":
        return None
    orders = user_orders.get(user_id)
    if not orders:
        return "❗️لا توجد طلبات لإرسالها."
    order_id = generate_order_id()
    summary = f"*🆔 رقم الطلب: {order_id}*\n"
    for service, order in orders.items():
        summary += f"\n📦 *{service}:*\n- {order}"
    save_order(order_id, user_id, orders)
    order_to_user[order_id] = user_id
    try:
        from mandoubs import mandoubs
        for m in mandoubs:
            send_message(m["id"], f"📦 طلب جديد من {user_id.replace('@c.us', '')}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")
    except ImportError:
        send_message("966503813344", f"📦 طلب جديد من {user_id.replace('@c.us', '')}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")
    for service, order in orders.items():
        vendor_msg = f"*طلب جديد - {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)
    user_orders.pop(user_id, None)
    msg = f"✅ تم تسجيل طلبك برقم *{order_id}*، بانتظار قبول مندوب. سيتم التواصل معك قريبًا."
    send_message(user_id, msg)
    return None

def handle_driver_accept_order(message, driver_id, user_states):
    if message.strip().startswith("قبول "):
        order_id = message.strip().split(" ", 1)[1]
        user_id = order_to_user.get(order_id)
        if user_id:
            order_to_driver[order_id] = driver_id
            user_states[user_id] = "awaiting_location"
            send_message(user_id, f"🚗 تم قبول طلبك (رقم {order_id}) من قبل المندوب. الرجاء إرسال موقعك الآن.")
            send_message(driver_id, f"✅ تم تسجيل قبولك للطلب رقم {order_id}. انتظر موقع العميل.")
            return "تمت معالجة قبول الطلب."
        else:
            send_message(driver_id, "🚫 لم يتم العثور على هذا الرقم.")
            return "لم يتم العثور على الطلب."
    return None

def handle_user_location(user_id, message, user_states, latitude=None, longitude=None):
    if user_states.get(user_id) == "awaiting_location":
        order_id = next((oid for oid, uid in order_to_user.items() if uid == user_id), None)
        if not order_id:
            send_message(user_id, "🚫 لم يتم العثور على رقم طلبك.")
            return "لا يوجد طلب بانتظار موقع."
        driver_id = order_to_driver.get(order_id)
        if not driver_id:
            send_message(user_id, "🚫 لم يتم العثور على المندوب المرتبط بالطلب.")
            return "لا يوجد مندوب مرتبط بالطلب."
        # إذا أرسل الموقع الصحيح (إحداثيات)
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
    # دعم استقبال "99" أو "٩٩" خارج الخدمة
    if message.strip() in ["99", "٩٩"]:
        # تحقق إذا المستخدم ليس في حالة انتظار خدمة
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
    # تم تمرير الإحداثيات هنا
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
            service_info["stores"]
        )
        if response:
            return response
    return None