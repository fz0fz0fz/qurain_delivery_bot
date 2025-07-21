from flask import Flask, request
from services import pharmacy
import requests

app = Flask(__name__)

TRIGGERS = ["0", "٠", ".", "صفر", "خدمات"]

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

@app.route("/", methods=["GET"])
def home():
    return "Qurain Bot ✅"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form.to_dict()
    sender = data.get("from")
    message = data.get("body", "").strip()

    print("👤", sender)
    print("💬", message)

    if message in TRIGGERS:
        send_whatsapp(sender, MAIN_MENU)
    elif message == "2":
        send_whatsapp(sender, pharmacy.get_menu())
    elif message == "99":
        send_whatsapp(sender, "📥 أرسل طلبك الآن، وسنقوم بتجهيزه لك بإذن الله.")
        # لاحقاً نضيف تخزين حالة الطلب
    else:
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
    print("تم الإرسال ✅" if response.ok else "❌", response.text)
