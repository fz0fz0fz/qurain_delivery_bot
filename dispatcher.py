from vendors import vendors
from mandoubs import mandoubs
from utils import generate_order_id
from order_router import manual_split
from services import pharmacy, grocery, vegetable
import requests

def send_whatsapp(to, message):
    url = "https://api.ultramsg.com/instance130542/messages/chat"
    payload = {
        "token": "9dxefhg0k4l3b7ak",
        "to": to,
        "body": message
    }
    response = requests.post(url, data=payload)
    print("✅ أُرسل إلى:", to, "→", "نجاح" if response.ok else "خطأ", response.text)

def process_order(customer_number, message):
    order_id = generate_order_id()
    split = manual_split(message)

    # إرسال الطلبات للمحلات
    if "pharmacy" in split:
        pharmacy.send_order(vendors["pharmacy"]["number"], order_id, split["pharmacy"])
    if "grocery" in split:
        grocery.send_order(vendors["grocery"]["number"], order_id, split["grocery"])
    if "vegetable" in split:
        vegetable.send_order(vendors["vegetable"]["number"], order_id, split["vegetable"])

    # إرسال للمندوب الأول المتاح
    for mandoub in mandoubs:
        if mandoub["available"]:
            msg = (
                f"📦 طلب جديد رقم {order_id} من 3 محلات:\n"
                f"هل تستطيع الاستلام؟ أرسل 1 للقبول."
            )
            send_whatsapp(mandoub["id"], msg)
            break

def dispatch_message(message, user_id):
    if not message or not user_id:
        print("❌ تم استلام بيانات غير صالحة:")
        print("message:", message)
        print("user_id:", user_id)
        return

    print(f"📩 رسالة جديدة من {user_id}: {message}")

    if message.strip() == "0":
        reply = (
            "✅ *أهلاً بك في دليل خدمات القرين*\n"
            "1️⃣ صيدلية 💊\n"
            "2️⃣ بقالة 🥤\n"
            "3️⃣ خضار 🥬\n"
            "99. اطلب الآن\n"
            "20. طلباتك"
        )
        send_whatsapp(user_id, reply)

    elif message.strip() == "99":
        send_whatsapp(user_id, "✏️ أرسل طلبك الآن، مثال:\nبندول، عصير، طماطم")

    elif message.strip().startswith("G"):
        send_whatsapp(user_id, "📦 تم استلام رقم طلبك بنجاح. شكراً لك.")

    else:
        process_order(user_id, message)
        send_whatsapp(user_id, "✅ تم استلام طلبك وسيتم التواصل معك قريباً.")
