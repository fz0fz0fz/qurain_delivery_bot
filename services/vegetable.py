from order_logger import get_user_state, set_user_state, log_order

def handle_vegetable(user_id, message):
    msg = message.strip()

    if msg == "4":
        return (
            "*[4] قائمة الخضار:*\n\n"
            "1- خضار المدينة\n"
            "2- خضار طازج\n"
            "3- خضار القرين\n\n"
            "*99 - إطلب*: أرسل طلبك ليُعرض في 'طلباتك'."
        )

    elif msg == "99" and get_user_state(user_id) is None:
        set_user_state(user_id, "awaiting_vegetable_order")
        return "🥬 أرسل طلبك الآن للخضار، وسيتم حفظه في 'طلباتك'."

    elif get_user_state(user_id) == "awaiting_vegetable_order":
        log_order(user_id, "الخضار", msg)
        set_user_state(user_id, None)
        return "✅ تم حفظ طلبك ضمن طلبات الخضار، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return "📌 يرجى اختيار رقم من القائمة أو إرسال 99 لإدخال الطلب."
