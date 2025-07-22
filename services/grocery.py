from order_logger import load_data, save_data

def handle_grocery(user_id, message):
    data = load_data()
    states = data["states"].setdefault(user_id, {})
    service_state = states.get("3", "main")  # state خاص لخدمة 3 (البقالة)

    msg = message.strip()
    print(f"📦 [GROCERY] المستخدم: {user_id}, الرسالة: {msg}")

    if msg == "3":
        states["3"] = "showing_stores"
        save_data(data)
        return (
            "*🛒 بقالات القرين:*\n"
            "1. بقالة السالم\n"
            "2. بقالة الراية\n"
            "3. بقالة التوفير\n"
            "99. اطلب الآن"
        )

    elif msg == "99" and service_state == "showing_stores":
        states["3"] = "awaiting_grocery_order"
        save_data(data)
        return "✏️ أرسل الآن طلبك الخاص بالبقالة مثل: عصير، شطة، بيبسي"

    elif service_state == "awaiting_grocery_order":
        log_order(user_id, "البقالة", msg)
        states["3"] = "main"
        save_data(data)
        return "✅ تم حفظ طلبك ضمن طلبات البقالة، أرسل 0 للرجوع للقائمة أو 20 لمراجعة طلباتك."

    return None
