from order_logger import get_user_state, set_user_state, log_order

def handle_grocery(user_id, message):
    msg = message.strip()

    if msg == "3":
        return (
            "*🛒 بقالات القرين:*\n"
            "1. بقالة السالم\n"
            "2. بقالة الراية\n"
            "3. بقالة التوفير\n"
            "99. اطلب الآن"
        )

    elif msg == "99" and get_user_state(user_id) is None:
        set_user_state(user_id, "awaiting_grocery_order")
        return "✏️ أرسل الآن طلبك الخاص بالبقالة مثل: عصير، شطة، بيبسي"

    elif get_user_state(user_id) == "awaiting_grocery_order":
        log_order(user_id, "البقالة", msg)
        set_user_state(user_id, None)
        return "✅ تم حفظ طلبك ضمن طلبات البقالة، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
