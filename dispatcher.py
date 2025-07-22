import random
from order_logger import load_data, save_data, log_order, get_all_orders, clear_user_orders, get_user_state, set_user_state, get_last_service, set_last_service
from send_utils import send_message, generate_order_id
from mandoubs import mandoubs
from vendors import vendors  # مدمج كـ STORE_NUMBERS
from services.pharmacy import handle_pharmacy
from services.grocery import handle_grocery
#chw أضف handle_vegetable إذا وجد

# قائمة الخدمات الكاملة
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

# قوائم المحلات (بناءً على handlers)
STORES = {
    "2": ["صيدلية الدواء", "صيدلية النهدي", "صيدلية زهرة"],
    "3": ["بقالة السالم", "بقالة الراية", "بقالة التوفير"],
    # أضف لـ 4 والباقي
}

# أرقام المحلات من vendors
STORE_NUMBERS = {
    "2": vendors.get("pharmacy", {}).get("number", ""),
    "3": vendors.get("grocery", {}).get("number", ""),
    "4": vendors.get("vegetable", {}).get("number", ""),
    # أضف الباقي
}

NO_REQUEST_SERVICES = ["1", "16"]

def dispatch_message(message, user_id):
    data = load_data()
    states = data["states"].setdefault(user_id, {})  # dict for per-service state
    msg = message.strip()

    # معالجة الرسائل من المندوب
    mandoub_ids = [m["id"] for m in mandoubs]
    if user_id in mandoub_ids:
        if msg.lower() == "موافق":
            data["states"][user_id] = "mandob_awaiting_location"
            send_message(user_id, "أرسل موقعك المباشر الآن (live location).")
            save_data(data)
            return
        if data["states"].get(user_id) == "mandob_awaiting_location":
            customer_id = data.get("client_for_mandoub", {}).get(user_id, "")
            if customer_id:
                send_message(customer_id, f"🔔 المندوب وافق! موقعه المباشر: {msg}")
            data["states"][user_id] = "main"
            save_data(data)
            return

    # القائمة الرئيسية
    if msg in ["0", ".", "٠", "خدمات", "القائمة"]:
        main_menu = "*🧾 خدمات القرين:*\n" + "\n".join([f"{k}. {v}" for k, v in SERVICES.items()])
        send_message(user_id, main_menu)
        return

    # عرض طلباتك
    if msg in ["20", "طلباتك"]:
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "🗃 لا يوجد طلبات محفوظة حاليًا.")
            return
        summary = "🗂 *ملخص طلباتك:*\n" + "\n".join([f"{i}. ({item['service']}) {item['order']}" for i, item in enumerate(orders, 1)])
        summary += "\n✅ أرسل *تم* للإرسال النهائي."
        send_message(user_id, summary)
        return

    # إنهاء الطلب ("تم")
    if msg.lower() == "تم":
        orders = get_all_orders(user_id)
        if not orders:
            send_message(user_id, "❌ لا يوجد طلبات لإرسالها.")
            return

        order_id = generate_order_id()
        combined = "\n".join([f"- ({o['service']}) {o['order']}" for o in orders])
        mandob_msg = f"🔔 طلب جديد (رقم {order_id}): \nمن: {user_id}\nالطلبات: {combined}\n📍 الموقع: (سيتم إرسال)\nرد 'موافق' لقبول."

        # اختيار مندوب متاح
        available = [m for m in mandoubs if m["available"]]
        if not available:
            send_message(user_id, "❌ لا مندوب متاح.")
            return
        selected = random.choice(available)["id"]
        send_message(selected, mandob_msg)

        # حفظ الربط بين المندوب والعميل
        data["client_for_mandoub"] = data.get("client_for_mandoub", {})
        data["client_for_mandoub"][selected] = user_id
        save_data(data)

        # نسخ مخصصة للمحلات
        service_orders = {}
        for o in orders:
            service_orders.setdefault(o["service"], []).append(o["order"])
        for service, items in service_orders.items():
            service_id = next((k for k, v in SERVICES.items() if v == service), None)
            if service_id in STORE_NUMBERS and STORE_NUMBERS[service_id]:
                store_msg = f"طلب جديد ({order_id}) من {user_id}:\n{', '.join(items)}"
                send_message(STORE_NUMBERS[service_id], store_msg)

        send_message(user_id, f"📤 تم إرسال طلبك بنجاح ✅\n*رقم الطلب: {order_id}*\nسيتم التواصل معك قريباً.\nأرسل موقعك الآن للتسليم (شارك موقعك من واتس آب).")
        data["states"][user_id]["global"] = "awaiting_customer_location"  # state عام للموقع
        save_data(data)
        clear_user_orders(user_id)
        return

    # معالجة موقع العميل
    if states.get("global", "") == "awaiting_customer_location":
        for mandoub_id, client in data.get("client_for_mandoub", {}).items():
            if client == user_id:
                send_message(mandoub_id, f" Baw موقع العميل للطلب {order_id}: {msg}")
                break
        states["global"] = "main"
        data["states"][user_id] = states
        save_data(data)
        send_message(user_id, "تم حفظ موقعك وإرساله للمندوب.")
        return

    # توزيع على handlers المحددة
    handlers = {
        "2": handle_pharmacy,
        "3": handle_grocery,
        # أضف handle_vegetable والباقي
    }
    if msg in handlers:
        response = handlers[msg](user_id, msg)
        if response:
            send_message(user_id, response)
            return

    # unified handler for other services (مشابهة لـ pharmacy/grocery)
    if msg in SERVICES and msg != "20":
        service_id = msg
        service_name = SERVICES[service_id]
        current_state = states.get(service_id, "main")

        if service_id in NO_REQUEST_SERVICES:
            send_message(user_id, f"هذه الخدمة ({service_name}) لا تحتاج طلبات. تواصل مباشرة مع المندوب.")
            return

        if current_state == "main":
            stores = STORES.get(service_id, [])
            if stores:
                stores_list = "\n".join(stores) + "\n99. اطلب الآن"
                states[service_id] = "choosing_store"
                data["states"][user_id] = states
                save_data(data)
                send_message(user_id, f"اختر محل من {service_name}:\n{stores_list}")
            else:
                states[service_id] = "Awaiting_order"
                data["states"][user_id] = states
                save_data(data)
                send_message(user_id, f"أرسل طلبك لـ {service_name} الآن (مثال: عنصر1 + عنصر2):")
            return

        elif current_state == "choosing_store":
            if msg == "99":
                states[service_id] = "awaiting_order"
                data["states"][user_id] = states
                save_data(data)
                send_message(user_id, "أرسل طلبك الآن:")
            else:
                # افتراض اختيار محل
                states[service_id] = "awaiting_order"
                data["states"][user_id] = states
                save_data(data)
                send_message(user_id, "تم اختيار المحل. أرسل طلبك:")
            return

        elif current_state == "awaiting_order":
            log_order(user_id, service_name, msg)
            states[service_id] = "main"
            data["states"][user_id] = states
            save_data(data)
            send_message(user_id, "✅ تم حفظ طلبك ضمن {service_name}، أرسل 0 للقائمة أو 20 للطلبات.")
            return

    # fallback
    send_message(user_id, "❓ لم أفهم، أرسل (0) للقائمة.")
