def dispatch_message(user_id, message, user_states, user_orders, driver_id=None, latitude=None, longitude=None):
    # دعم استقبال "99" أو "٩٩" خارج الخدمة
    if message.strip() in ["99", "٩٩"]:
        # تحقق إذا المستخدم ليس في حالة انتظار خدمة
        if not any(
            user_states.get(user_id, "").startswith("awaiting_order_")
            for user_id in [user_id]
        ):
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."
    response = handle_main_menu(message)
    if response: return response
    response = handle_feedback(user_id, message, user_states)
    if response: return response
    response = handle_view_orders(user_id, message, user_orders)
    if response: return response
    response = handle_finalize_order(user_id, message, user_orders)
    if response: return response
    if driver_id:
        response = handle_driver_accept_order(message, driver_id, user_states)
        if response: return response
    # تم تمرير الإحداثيات هنا
    response = handle_user_location(user_id, message, user_states, latitude=latitude, longitude=longitude)
    if response: return response
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