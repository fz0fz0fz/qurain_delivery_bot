from send_utils import send_message, generate_order_id
from order_logger import save_order

# حالة المستخدم 100 للشكوى أو الاقتراح
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

# استقبال كلمة "تم" لإرسال الطلب
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

    # حفظ الطلب
    save_order(order_id, user_id, orders)

    # إرسال للمندوب (رقم افتراضي)
    send_message("966503813344", f"📦 طلب جديد من {user_id}:\n\n{summary}")

    # إرسال للعميل
    send_message(user_id, f"✅ تم إرسال طلبك بنجاح، رقم الطلب هو *{order_id}*")

    # إرسال لكل محل حسب القسم
    for service, order in orders.items():
        vendor_msg = f"*طلب جديد - {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)  # غيّر الرقم عند الربط الفعلي

    user_orders.pop(user_id, None)
    return None
