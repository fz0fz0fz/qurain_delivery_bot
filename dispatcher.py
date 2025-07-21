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
