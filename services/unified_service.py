# services/unified_service.py

from order_logger import (
    log_order,
    get_user_state,
    set_user_state,
    get_last_service,
    set_last_service
)

def handle_service(user_id, message, service_id, service_name, stores_list):
    msg = message.strip()
    state = get_user_state(user_id)
    last_service = get_last_service(user_id)

    # عرض قائمة المحلات
    if msg == service_id:
        set_last_service(user_id, service_name)
        response = f"*📦 {service_name}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # بدء الطلب
    elif msg == "99" and state is None and last_service == service_name:
        set_user_state(user_id, f"awaiting_order_{service_name}")
        return f"✏️ أرسل الآن طلبك الخاص بـ {service_name}، مثال: (اسم المنتج أو الطلب)"

    # استقبال الطلب الفعلي
    elif state == f"awaiting_order_{service_name}":
        log_order(user_id, service_name, msg)  # تخزين الطلب
        set_user_state(user_id, None)
        return f"✅ تم حفظ طلبك ضمن طلبات {service_name}.\nأرسل (0) للرجوع للقائمة أو (20) لمراجعة طلباتك."

    return None
