def handle_service(user_id, message, user_states, user_orders, service_id, service_name, stores_list):
    msg = message.strip()

    # دخول المستخدم على الخدمة (مثل 2 أو 3)
    if msg == service_id:
        user_states[user_id] = f"awaiting_order_{service_name}"  # ✅ تعيين الحالة
        response = f"*📦 {service_name}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # المستخدم أرسل 99 لبدء الطلب
    elif msg == "99" and user_states.get(user_id) == f"awaiting_order_{service_name}":
        return f"✏️ أرسل الآن طلبك الخاص بـ {service_name}، مثال: (اسم المنتج أو الطلب)"

    # المستخدم أرسل الطلب فعليًا
    elif user_states.get(user_id) == f"awaiting_order_{service_name}":
        user_states.pop(user_id, None)
        user_orders.setdefault(user_id, {})[service_name] = msg
        print("✅ تم حفظ الطلب:", user_orders)
        return f"✅ تم حفظ طلبك: {msg}"

    return None
