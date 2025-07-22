from order_logger import get_user_state, set_user_state, log_order

def handle_pharmacy(user_id, message):
    msg = message.strip()

    if msg == "2":
        return (
            "*📦 صيدليات القرين:*\n"
            "1. صيدلية الدواء\n"
            "2. صيدلية النهدي\n"
            "3. صيدلية زهرة\n"
            "99. اطلب الآن"
        )

    elif msg == "99" and get_user_state(user_id) is None:
        set_user_state(user_id, "awaiting_pharmacy_order")
        return "✏️ أرسل الآن طلبك الخاص بالصيدلية مثل: بندول، فيتامين د"

    elif get_user_state(user_id) == "awaiting_pharmacy_order":
        log_order(user_id, "الصيدلية", msg)
        set_user_state(user_id, None)
        return "✅ تم حفظ طلبك ضمن طلبات الصيدلية، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
