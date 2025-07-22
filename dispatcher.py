import random
from order_logger import load_data, save_data, log_order, get_all_orders, clear_user_orders
from send_utils import send_message, generate_order_id
from mandoubs import mandoubs
from vendors import vendors

# Handlers from services
from services.pharmacy import handle_pharmacy
from services.grocery import handle_grocery
# أضف handle_vegetable if exists

SERVICES = {
    "1": "حكومي",
    "2": "صيدلية 💊",
    "3": "بقالة 🥤",
    "4": "خضار 🥬",
    "5": "رحلات ⛺️",
    "6": "حلا 🍮",
    "7": "أسر منتجة 🥧",
    "8": "مطاعم 🍔",
    "9": "قرطاسية 📗",
    "10": "محلات 🏪",
    "11": "شالية 🏖",
    "12": "وايت 🚛",
    "13": "شيول 🚜",
    "14": "دفان 🏗",
    "15": "مواد بناء وعوازل 🧱",
    "16": "عمال 👷",
    "17": "محلات مهنية 🔨",
    "18": "ذبائح وملاحم 🥩",
    "19": "نقل مدرسي ومشاوير 🚍",
    "20": "طلباتك"
}

STORE_NUMBERS = {
    "2": vendors["pharmacy"]["number"],
    "3": vendors["grocery"]["number"],
    "4": vendors["vegetable"]["number"],
    # Add more
}

NO_REQUEST_SERVICES = ["1", "16"]

def dispatch_message(message, user_id):
    data = load_data()
    states = data["states"].setdefault(user_id, {})  # Per-user state dict

    # Mandoub handling
    mandoub_ids = [m["id"] for m in mandoubs]
    if user_id in mandoub_ids:
        msg = message.strip().lower()
        if msg == "موافق":
            states["mandob_state"] = "awaiting_location"
            save_data(data)
            send_message(user_id, "أرسل موقعك المباشر.")
            return
        if states.get("mandob_state") == "awaiting_location":
            customer_id = data.get("customer_for_order", {}).get(user_id, "")
            if customer_id:
                send_message(customer_id, f"المندوب وافق! موقعه: {message}")
            states["mandob_state"] = None
            save_data(data)
            return

    msg = message.strip()

    if msg in ["0", "خدمات", "القائمة"]:
        main_menu = "*🧾 خدمات القرين:*\n" + "\n".join([f"{k}. {v}" for k, v in SERVICES.items()])
        send_message(user_id, main_menu)
        return

    # Service dispatching with per-service state
    if msg in SERVICES and msg != "20":
        service_id = msg
        service_name = SERVICES[service_id]
        service_state = states.get(service_id, "main")

        if service_id in NO_REQUEST_SERVICES:
            send_message(user_id, f"هذه الخدمة ({service_name}) لا تحتاج طلبات.")
            return

        if service_state == "main":
            # Handler-specific or unified
            handler = {
                "2": handle_pharmacy,
                "3": handle_grocery,
                # Add more
            }.get(service_id)
            if handler:
                response = handler(user_id, message)
            else:
                response = f"أرسل طلبك لـ {service_name}."
                states[service_id] = "awaiting_order"
                save_data(data)
            if response:
                send_message(user_id, response)
            return

        if service_state == "awaiting_order":
            log_order(user_id, service_name, msg)
            states[service_id] = "main"
            save_data(data)
            send_message(user_id, "تم حفظ الطلب.")
            return

    if msg == "20":
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "لا طلبات.")
            return
        summary = "ملخص الطلبات:\n" + "\n".join([f"({o['service']}) {o['order']}" for o in orders])
        send_message(user_id, summary + "\nأرسل تم للإرسال.")
        return

    if msg.lower() == "تم":
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "لا طلبات.")
            return

        order_id = generate_order_id()
        combined = "\n".join([f"({o['service']}) {o['order']}" for o in orders])
        mandob_msg = f"طلب جديد {order_id}: {combined}\nرد موافق."

        available = [m for m in mandoubs if m["available"]]
        if available:
            selected = random.choice(available)["id"]
            send_message(selected, mandob_msg)
            data["customer_for_order"] = data.get("customer_for_order", {})
            data["customer_for_order"][selected] = user_id
            save_data(data)

        # Customized copies to stores
        service_orders = {}
        for o in orders:
            service_orders.setdefault(o["service"], []).append(o["order"])
        for service, items in service_orders.items():
            service_id = next((k for k, v in SERVICES.items() if v == service), None)
            if service_id in STORE_NUMBERS:
                store_msg = f"طلب {order_id}: {', '.join(items)}"
                send_message(STORE_NUMBERS[service_id], store_msg)

_OPEN        send_message(user_id, f"تم الإرسال {order_id}. أرسل موقعك.")
        states["global"] = "awaiting_location"
        clear_user_orders(user_id)
        save_data(data)
        return

    if states.get("global") == "awaiting_location":
        for mandoub_id, customer in data.get("customer_for_order", {}).items():
            if customer == user_id:
                send_message(mandoub_id, f"موقع العميل: {msg}")
                break
        states["global"] = None
        save_data(data)
        send_message(user_id, "تم إرسال الموقع.")
        return

    send_message(user_id, "لم أفهم. أرسل 0.")
