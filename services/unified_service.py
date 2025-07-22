# services/unified_service.py

from order_logger import (
    get_user_state,
    set_user_state,
    log_order
)

def handle_service(user_id, message, service_id, service_name, stores_list):
    msg = message.strip()

    # عرض قائمة المحلات
    if msg == service_id:
        response = f"*📦 {service_name}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # بدء الطلب
    elif msg == "99" and get_user_state(user_id) is None:
        set_user_state(user_id, f"awaiting_order_{service_name}")
        return f"✏️ أرسل الآن طلبك الخاص بـ {service_name}، مثال: (اسم المنتج أو الطلب)"

    # استقبال الطلب الفعلي
    elif get_user_state(user_id) == f"awaiting_order_{service_name}":
        log_order(user_id, service_name, msg)
        set_user_state(user_id, None)
        return f"✅ تم حفظ طلبك ضمن طلبات {service_name}.\nأرسل (0) للرجوع للقائمة أو (20) لمراجعة طلباتك."

    return None
