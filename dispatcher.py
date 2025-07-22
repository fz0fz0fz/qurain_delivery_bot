from services.pharmacy import handle_pharmacy
from services.grocery import handle_grocery
from services.vegetable import handle_vegetable
from send_utils import send_message, generate_order_id
from order_logger import get_all_orders

def dispatch_message(message, user_id):
    if not message or not user_id:
        print("❌ بيانات غير صالحة:")
        print("message:", message)
        print("user_id:", user_id)
        return

    print(f"📩 رسالة جديدة من {user_id}: {message}")

    msg = message.strip()

    if msg == "0":
        reply = (
            "✅ *أهلاً بك في دليل خدمات القرين*\n"
            "1️⃣ حكومي\n"
            "2️⃣ صيدلية 💊\n"
            "3️⃣ بقالة 🥤\n"
            "4️⃣ خضار 🥬\n"
            "99. اطلب الآن\n"
            "20. طلباتك"
        )
        send_message(user_id, reply)
        return

    elif msg == "20":
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "📭 لا توجد طلبات محفوظة.")
            return

        order_text = "*🧾 طلباتك الحالية:*\n"
        for i, item in enumerate(orders, 1):
            order_text += f"{i}. [{item['service']}] {item['order']}\n"
        order_text += "\n✉️ أرسل (تم) لإرسال الطلب للمندوب."
        send_message(user_id, order_text)
        return

    elif msg == "تم":
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "📭 لا توجد طلبات لإرسالها.")
            return

        order_id = generate_order_id()
        summary = f"📦 *طلب جديد {order_id}:*\n"
        for i, item in enumerate(orders, 1):
            summary += f"{i}. [{item['service']}] {item['order']}\n"

        send_message(user_id, summary)
        # send_message("رقم_مندوب", summary)  # تفعيل لاحقًا
        from order_logger import clear_user_orders
        clear_user_orders(user_id)

        send_message(user_id, f"✅ تم إرسال طلبك بنجاح. رقم الطلب: {order_id}")
        return

    # توزيع الرسالة على الخدمات حسب الرقم
    for handler in (handle_pharmacy, handle_grocery, handle_vegetable):
        response = handler(user_id, message)
        if response:
            send_message(user_id, response)
            return

    # إذا لم يتم التعرف على الرسالة
    send_message(user_id, "❓ لم أفهم رسالتك، أرسل (0) لعرض القائمة.")
