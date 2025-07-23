
import random
from order_logger import load_data, save_data, log_order, get_all_orders, clear_user_orders
from send_utils import send_message, generate_order_id
from mandoubs import mandoubs
from vendors import vendors
from unified_service import handle_service

SERVICES = {
    "1": "حكومي 🏢",
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

NO_REQUEST_SERVICES = ["1", "16"]

def dispatch_message(message, user_id):
    data = load_data()
    states = data["states"]
    orders = data["orders"]
    msg = message.strip()

    # شكوى
    if msg == "100":
        send_message("966503813344", f"💬 شكوى من {user_id}:\n{msg}")
        send_message(user_id, "✉️ تم تحويل شكواك للإدارة، شكرًا لك.")
        return

    # مناديب
    mandoub_ids = [m["id"] for m in mandoubs]
    if user_id in mandoub_ids:
        if msg == "موافق":
            states[user_id] = {"mandob_state": "awaiting_location"}
            save_data(data)
            send_message(user_id, "أرسل موقعك المباشر.")
            return
        elif states.get(user_id, {}).get("mandob_state") == "awaiting_location":
            customer_id = data.get("customer_for_order", {}).get(user_id, "")
            if customer_id:
                send_message(customer_id, f"📍 موقع المندوب:\n{msg}")

            states[user_id]["mandob_state"] = None
            save_data(data)
            return

    # القائمة الرئيسية
    if msg in ["0", "خدمات", ".", "٠", "صفر", "القائمة"]:
        menu = "*🧾 خدمات القرين:*\n" + "\n".join([f"{k}. {v}" for k, v in SERVICES.items()])
        send_message(user_id, menu)
        return

    # عرض الطلبات
    if msg == "20":
        user_orders = orders.get(user_id, [])
        if user_orders:
            response = "*📝 طلباتك الحالية:*
" + "\n".join([f"- {o}" for o in user_orders])
        else:
            response = "📭 لا يوجد طلبات محفوظة حتى الآن."
        send_message(user_id, response)
        return

    # خدمة محددة
    for sid, sname in SERVICES.items():
        stores = vendors.get(sid, {}).get("stores", [])
        response = handle_service(user_id, msg, states, orders, sid, sname, stores)
        if response:
            save_data(data)
            send_message(user_id, response)
            return

    # غير مفهومة
    send_message(user_id, "❓ لم أفهم، أرسل (0) للقائمة.")
