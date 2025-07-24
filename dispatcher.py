from send_utils import send_message, generate_order_id
from order_logger import save_order
from services.unified_service import handle_service


# عرض القائمة الرئيسية عند إرسال "0" أو "." أو "٠" أو "خدمات"
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

# معالجة الشكاوى أو الاقتراحات
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

# إنهاء الطلبات
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

    # إرسال للمندوب
    send_message("966503813344", f"📦 طلب جديد من {user_id}:\n\n{summary}")

    # إرسال لكل محل حسب القسم
    for service, order in orders.items():
        vendor_msg = f"*طلب جديد - {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)

    # حذف الطلبات بعد الإرسال
    user_orders.pop(user_id, None)

    # إرسال للعميل + رد ظاهر له
    msg = f"✅ تم إرسال طلبك بنجاح، رقم الطلب هو *{order_id}*"
    send_message(user_id, msg)
    return msg

# ✅ الدالة الرئيسية التي تُستخدم في app.py
def dispatch_message(user_id, message, user_states, user_orders):
    # القائمة الرئيسية
    response = handle_main_menu(message)
    if response:
        return response

    # الشكاوى
    response = handle_feedback(user_id, message, user_states)
    if response:
        return response

    # عرض الطلبات
    response = handle_view_orders(user_id, message, user_orders)
    if response:
        return response

    # إنهاء الطلبات
    response = handle_finalize_order(user_id, message, user_orders)
    if response:
        return response

    # الخدمات الموحدة مثل صيدلية، بقالة، خضار
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

    return None  # لا يوجد رد مفهوم
