# dispatcher.py

from send_utils import send_message, generate_order_id
from order_logger import save_order, load_orders, save_all_orders
from unified_service import handle_service
from mandoubs import get_next_mandoub

# عرض القائمة الرئيسية
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

# الشكاوى والاقتراحات
def handle_feedback(user_id, message, user_states):
    if message.strip() == "100":
        user_states[user_id] = "awaiting_feedback"
        return "✉️ أرسل الآن رسالتك (اقتراح أو شكوى)"
    elif user_states.get(user_id) == "awaiting_feedback":
        user_states.pop(user_id, None)
        send_message("966503813344", f"💬 شكوى من {user_id}:\n{message}")
        return "✅ تم استلام رسالتك، شكرًا لك."
    return None

# عرض الطلبات السابقة
def handle_view_orders(user_id, message, user_orders):
    if message.strip() == "20":
        orders = user_orders.get(user_id, {})
        if not orders:
            return "📭 لا توجد طلبات محفوظة حتى الآن."
        
        response = "*🗂 طلباتك المحفوظة:*\n"
        for service, order in orders.items():
            response += f"\n📌 *{service}:*\n- {order}"
        response += "\n\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
        return response
    return None

# إرسال الطلب إلى المندوب المناسب
def send_order_to_next_mandoub(order_id):
    orders_data = load_orders()
    order = orders_data.get("orders", {}).get(order_id)

    if not order:
        print(f"❌ الطلب {order_id} غير موجود.")
        return

    sent_to = order.get("sent_to", [])
    next_mandoub = get_next_mandoub(sent_to)

    if not next_mandoub:
        print("🚫 لا يوجد مناديب متاحين لإرسال الطلب.")
        return

    # بناء الطلب الكامل لكل الأقسام
    msg = f"*📦 طلب جديد - رقم الطلب: {order_id}*\n"
    for service, service_order in order["orders"].items():
        msg += f"\n📌 *{service}:*\n- {service_order}"

    send_message(next_mandoub, msg)

    # تحديث سجل الطلب
    order["sent_to"].append(next_mandoub)
    save_all_orders(orders_data)
    print(f"✅ تم إرسال الطلب {order_id} إلى {next_mandoub}")

# إنهاء الطلبات وإرسالها
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

    send_order_to_next_mandoub(order_id)

    user_orders.pop(user_id, None)

    send_message(user_id, f"✅ تم إرسال طلبك بنجاح، رقم الطلب هو *{order_id}*")
    return f"✅ تم إرسال طلبك بنجاح، رقم الطلب هو *{order_id}*"

# ✅ الدالة الرئيسية
def dispatch_message(user_id, message, user_states, user_orders):
    response = handle_main_menu(message)
    if response:
        return response

    response = handle_feedback(user_id, message, user_states)
    if response:
        return response

    response = handle_view_orders(user_id, message, user_orders)
    if response:
        return response

    response = handle_finalize_order(user_id, message, user_orders)
    if response:
        return response

    # الخدمات الموحدة
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
