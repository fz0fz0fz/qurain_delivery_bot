from services.unified_service import handle_service
from send_utils import send_message, generate_order_id
from mandoubs import mandoubs
from order_logger import save_order

services = {
    "2": {
        "name": "الصيدلية",
        "stores": ["صيدلية الدواء", "صيدلية النهدي", "صيدلية زهرة"]
    },
    "3": {
        "name": "البقالة",
        "stores": ["بقالة التميمي", "بقالة الخير", "بقالة المدينة"]
    },
    "4": {
        "name": "الخضار",
        "stores": ["خضار الطازج", "سوق المزارعين", "خضار الوفرة"]
    }
}

def dispatch_message(user_id, message, user_states, user_orders):
    msg = message.strip()

    # عرض القائمة الرئيسية
    if msg in ["0", ".", "٠", "صفر", "خدمات"]:
        user_states[user_id] = "main_menu"
        return """*📋 قائمة خدمات القرين:*

2. صيدلية 💊
3. بقالة 🥤
4. خضار 🥬
20. طلباتك"""

    # عرض الطلبات المحفوظة
    elif msg == "20":
        return show_saved_orders(user_id, user_orders)

    # تأكيد إرسال الطلب النهائي
    elif msg == "تم":
        return handle_finalize_order(user_id, user_orders, user_states)

    # التوجيه للخدمة المناسبة
    for code, service in services.items():
        response = handle_service(
            user_id=user_id,
            message=msg,
            user_states=user_states,
            user_orders=user_orders,
            service_id=code,
            service_name=service["name"],
            stores_list=service["stores"]
        )
        if response:
            return response

    return "🤖 عذرًا، لم أفهم رسالتك. أرسل (0) لعرض قائمة الخدمات."

def show_saved_orders(user_id, user_orders):
    if user_id not in user_orders or not user_orders[user_id]:
        return "📭 لا توجد طلبات محفوظة حالياً."

    orders = user_orders[user_id]
    response = "*🗂 طلباتك المحفوظة:*\n"
    for service, order in orders.items():
        response += f"\n📌 *{service}:*\n- {order}"
    response += "\n\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
    return response

def handle_finalize_order(user_id, user_orders, user_states):
    if user_id not in user_orders or not user_orders[user_id]:
        return "📭 لا توجد طلبات محفوظة."

    orders = user_orders[user_id]
    order_id = generate_order_id()

    # حفظ الطلب النهائي
    save_order(order_id, user_id, orders)

    # إنشاء ملخص للطلب الكامل للمندوب
    summary = f"*📦 طلب جديد - رقم الطلب: {order_id}*\n"
    for service, order in orders.items():
        summary += f"\n📌 *{service}:*\n- {order}"

    # إرسال للمندوبين
    for mandoub in mandoubs:
        send_message(mandoub, summary)

    # إرسال رسالة خاصة لكل قسم (بدون تكرار)
    for service, order in orders.items():
        vendor_msg = f"*📦 طلب جديد خاص بقسم {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)  # ← عدل الرقم لاحقًا

    # حذف الطلبات بعد الإرسال
    del user_orders[user_id]
    user_states[user_id] = "main_menu"
    return f"✅ تم إرسال طلبك بنجاح، رقم الطلب هو *{order_id}*"
