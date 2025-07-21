def handle_grocery(user_id, message, user_states, user_orders):
    if message.strip() == "3":
        return (
            "*🛒 بقالات القرين:*\n"
            "1. بقالة السالم\n"
            "2. بقالة الراية\n"
            "3. بقالة التوفير\n"
            "99. اطلب الآن"
        )

    elif message.strip() == "99":
        user_states[user_id] = "awaiting_grocery_order"
        return "✏️ أرسل الآن طلبك الخاص بالبقالة مثل: عصير، شطة، بيبسي"

    elif user_states.get(user_id) == "awaiting_grocery_order":
        # حفظ الطلب في قائمة الطلبات مع اسم الخدمة
        user_orders.setdefault(user_id, []).append({
            "service": "البقالة",
            "order": message
        })
        user_states[user_id] = None
        return "✅ تم حفظ طلبك ضمن طلبات البقالة، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
