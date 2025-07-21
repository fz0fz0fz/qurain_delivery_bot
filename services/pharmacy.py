from state import user_states, user_orders

pharmacies = [
    "صيدلية النهدي",
    "صيدلية الدواء",
    "صيدلية المدينة",
    "صيدلية فارمسي ون"
]

def handle_pharmacy(sender, msg, state_map):
    if msg == "2":
        return (
            "*💊 صيدليات القرين:*\n\n"
            + "\n".join(f"{i+1}. {pharmacy}" for i, pharmacy in enumerate(pharmacies))
            + "\n\n99 - اطلب الآن"
        )

    elif msg == "99":
        state_map[sender] = "awaiting_pharmacy_order"
        return "✍️ اكتب طلبك الخاص بالصيدلية الآن..."

    else:
        return "📌 يرجى اختيار صيدلية من القائمة أو إرسال 99 لطلب خاص."

def save_pharmacy_order(sender, order):
    if sender not in user_orders:
        user_orders[sender] = []
    user_orders[sender].append(f"[صيدلية] {order}")
