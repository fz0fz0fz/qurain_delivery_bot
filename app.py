from flask import Flask, request
import requests

app = Flask(__name__)

# قائمة الكلمات التي تفتح القائمة الرئيسية
TRIGGERS = ["0", "٠", ".", "صفر", "خدمات"]

# القائمة الرئيسية
MAIN_MENU = """📍 *دليل خدمات القرين* 📍

1️⃣. حكومي
2️⃣. صيدلية 💊
3️⃣. بقالة 🥤
4️⃣. خضار 🥬
5️⃣. رحلات ⛺️
6️⃣. حلا 🍮
7️⃣. أسر منتجة 🥧
8️⃣. مطاعم 🍔
9️⃣. قرطاسية 📗
🔟. محلات 🏪
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

أرسل رقم الخدمة للاطلاع على التفاصيل 👇
"""

@app.route('/', methods=['GET'])
def home():
    return "Qurain Delivery Bot is running ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form.to_dict()
    full_data = request.get_json(force=True)
    print("📥 البيانات المستلمة:", full_data)

    sender = full_data.get("data", {}).get("from")
    message = full_data.get("data", {}).get("body")

    print("👤 المرسل:", sender)
    print("💬 الرسالة:", message)

    if not sender or not message:
        return "No sender/message", 400

    # الرد التلقائي على "خدمات"
    if message.strip() in TRIGGERS:
        send_whatsapp(sender, MAIN_MENU)
        return "OK", 200

    # الرد الافتراضي لو احتجنا لاحقًا
    send_whatsapp(sender, f"📩 تم استلام رسالتك: {message}")
    return "OK", 200

def send_whatsapp(to, message):
    url = "https://api.ultramsg.com/instance130542/messages/chat"
    payload = {
        "token": "9dxefhg0k4l3b7ak",
        "to": to,
        "body": message
    }
    response = requests.post(url, data=payload)
    print("تم الإرسال إلى:", to, "✅" if response.ok else "❌", response.text)
