
from vendors import vendors
from mandoubs import mandoubs
from utils import generate_order_id
from order_router import manual_split
from services import pharmacy, grocery, vegetable

def send_whatsapp(to, message):
    print(f"رسالة إلى {to}: {message}")

def process_order(customer_number, message):
    order_id = generate_order_id()
    split = manual_split(message)

    if "pharmacy" in split:
        pharmacy.send_order(vendors["pharmacy"]["number"], order_id, split["pharmacy"])
    if "grocery" in split:
        grocery.send_order(vendors["grocery"]["number"], order_id, split["grocery"])
    if "vegetable" in split:
        vegetable.send_order(vendors["vegetable"]["number"], order_id, split["vegetable"])

    for mandoub in mandoubs:
        if mandoub["available"]:
            send_whatsapp(mandoub["id"], f"📦 طلب جديد رقم {order_id} من 3 محلات.
هل تستطيع الاستلام؟ أرسل 1 للقبول.")
            break
