from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

ULTRA_TOKEN = "9dxefhg0k4l3b7ak"
INSTANCE_ID = "instance130542"
API_URL = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

orders_file = "orders_log.json"

# تهيئة ملف الطلبات
if not os.path.exists(orders_file):
    with open(orders_file, "w") as f:
        json.dump({}, f)

@app.route('/')
def home():
    return "Qurain Delivery Bot ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form.to_dict()
    sender = data.get('from')
    message = data.get('body', '').strip()

    print("📥 البيانات المستلمة:", data)
    print("👤 المرسل:", sender)
    print("💬 الرسالة:", message)

    if not sender or not message:
        return "Missing data", 400

    if message in ['0', '.', '٠', 'صفر', 'خدمات']:
        send_main_menu(sender)

    elif message == "2":
        send_pharmacy_menu(sender)

    elif message == "99":
        handle_order_request(sender)

    else:
        save_order(sender, message)

    return "OK", 200

def send_main_menu(to):
    menu = """📋 *دليل خدمات القرين:*

1️⃣. حكومي
2️⃣. صيدلية 💊
3️⃣. بقالة 🥤
4️⃣. خضار 🥬
5️⃣. رحلات ⛺️
6️⃣. حلا 🍮
7️⃣. أسر منتجة 🥧
8️⃣. مطاعم 🍔
9️⃣. قرطاسية 📗
1️⃣0️⃣. محلات 🏪
1️⃣1️⃣. شالية 🏖
1️⃣2️⃣. وايت 🚛
1️⃣3️⃣. شيول 🚜
1️⃣4️⃣. دفان 🏗
1️⃣5️⃣. مواد بناء وعوازل 🧱
1️⃣6️⃣. عمال 👷
1️⃣7️⃣. محلات مهنية 🔨
1️⃣8️⃣. ذبائح وملاحم 🥩
1️⃣9️⃣. نقل مدرسي ومشاوير 🚍
2️⃣0️⃣. طلباتك

*لرؤية خدمات الصيدليات أرسل:* 2
*لطلب فوري أرسل:* 99"""
    send_whatsapp(to, menu)

def send_pharmacy_menu(to):
    msg = """*[2]* *قائمة الصيدليات*:
1- صيدلية ركن أطلس (القرين)
2- صيدلية دواء البدر (الدليمية)
3- صيدلية ساير (الدليمية)

*99 - إطلب* : ستجد طلباتك كاملة في رقم 20 من القائمة الرئيسية."""
    send_whatsapp(to, msg)

def handle_order_request(sender):
    orders = load_orders()
    user_order = orders.get(sender)
    if user_order:
        reply = "🧺 أرسل طلبك الآن، وسنقوم بتجهيزه لك بإذن الله."
    else:
        reply = "❌ لا يوجد طلب مسجل لك حاليًا. الرجاء إرسال طلبك أولاً."
    send_whatsapp(sender, reply)

def save_order(sender, message):
    orders = load_orders()
    orders[sender] = message
    with open(orders_file, "w") as f:
        json.dump(orders, f)

def load_orders():
    with open(orders_file, "r") as f:
        return json.load(f)

def send_whatsapp(to, message):
    payload = {
        "token": ULTRA_TOKEN,
        "to": to,
        "body": message
    }
    response = requests.post(API_URL, data=payload)
    print("تم الإرسال ✅", response.text)
