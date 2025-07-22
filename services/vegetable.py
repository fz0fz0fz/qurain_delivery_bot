from order_logger import get_user_state, set_user_state, log_order

def handle_vegetable(user_id, message):
    msg = message.strip()
    print(f"🥬 [VEGETABLE] المستخدم: {user_id}, الرسالة: {msg}")

    if msg == "4":
        return (
            "*🥦 خضار القرين:*\n"
            "1. خضار النعيم\n"
            "2. خضار البركة\n"
            "3. خضار الفصول الأربعة\n"
            "99. اطلب الآن"
        )

    elif msg == "99" and get_user_state(user_id) is None:
        set_user_state(user_id, "awaiting_vegetable_order")
        return "✏️ أرسل الآن طلبك الخاص بالخضار مثل: طماطم، خيار، جزر"

    elif get_user_state(user_id) == "awaiting_vegetable_order":
        log_order(user_id, "الخضار", msg)
        set_user_state(user_id, None)
        return "✅ تم حفظ طلبك ضمن طلبات الخضار، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
