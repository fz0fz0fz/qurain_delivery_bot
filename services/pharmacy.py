def handle_pharmacy(user_id, message, user_states, user_orders):
    if message.strip() == "2":
        return (
            "*📦 صيدليات القرين:*\n"
            "1. صيدلية الدواء\n"
            "2. صيدلية النهدي\n"
            "3. صيدلية زهرة\n"
            "99. اطلب الآن"
        )

    elif message.strip() == "99":
        user_states[user_id] = "awaiting_pharmacy_order"
        return "✏️ أرسل الآن طلبك الخاص بالصيدلية مثل: بندول، فيتامين د"

    elif user_states.get(user_id) == "awaiting_pharmacy_order":
        # حفظ الطلب في قائمة الطلبات مع اسم الخدمة
        user_orders.setdefault(user_id, []).append({
            "service": "الصيدلية",
            "order": message
        })
        user_states[user_id] = None
        return "✅ تم حفظ طلبك ضمن طلبات الصيدلية، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
