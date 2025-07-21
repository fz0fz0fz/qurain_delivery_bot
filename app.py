from flask import Flask, request
import requests

app = Flask(__name__)

# 🔁 الكلمات التي تستدعي القائمة الرئيسية
TRIGGERS = ["0", ".", "٠", "صفر", "خدمات"]

# 🧾 القائمة الرئيسية
MAIN_MENU = """*📋 قائمة خدمات القرين:*

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

اكتب رقم الخدمة أو "0" لعرض القائمة.
"""

# 🩺 قائمة الصيدليات كمثال
PHARMACY_MENU = """*[2] قائمة الصيدليات:*

1- صيدلية ركن أطلس (القرين)
__________________________
2- صيدلية دواء البدر (الدليمية)
__________________________
3- صيدلية ساير (الدليمية)

*99 - إطلب*: ستجد طلباتك في رقم 20 من القائمة الرئيسية.
"""

@app.route('/')
def home():
    return "Qurain Delivery Bot is running ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    full_data = request.get_json(force=True)
    print("📥 البيانات المستلمة:", full_data)

    inner_data = full_data.get("data", {})
    sender = inner_data.get("from")
    message = inner_data.get("body")

    print("👤 المرسل:", sender)
    print("💬 الرسالة:", message)

    if not sender:
        return "No sender", 400

    # الردود التلقائية حسب الرسالة
    if message in TRIGGERS:
        send_whatsapp(sender, MAIN_MENU)
    elif message == "2":
        send_whatsapp(sender, PHARMACY_MENU)
    elif message == "99":
        send_whatsapp(sender, "📥 أرسل طلبك الآن، وسنقوم بتجهيزه لك بإذن الله.")
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
    print("📤 تم الإرسال إلى:", to, "✅" if response.ok else "❌", response.text)
