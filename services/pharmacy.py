from utils import send_message

pharmacies = [
    "صيدلية النهدي",
    "صيدلية الدواء",
    "صيدلية المدينة",
    "صيدلية فارمسـي ون"
]

def handle_pharmacy(user_id, message, user_states, user_orders):
    if user_states.get(user_id) == "awaiting_pharmacy_order":
        # المستخدم أرسل الطلب بعد 99
        user_orders.setdefault(user_id, []).append({
            "service": "الصيدلية",
            "order": message
        })
        user_states[user_id] = None
        return "📌 تم حفظ طلبك في قسم (طلباتك)."

    if message in ["2", "02", "٢"]:
        reply = "💊 *صيدليات القرين:*\n"
        for i, name in enumerate(pharmacies, 1):
            reply += f"{i}. {name}\n"
        reply += "\n*99 - اطلب الآن*"
        return reply

    if message == "99":
        user_states[user_id] = "awaiting_pharmacy_order"
        return "📝 أرسل الآن طلبك الخاص بالصيدلية، وسنحفظه لك في قسم (طلباتك) رقم 20."

    return None
