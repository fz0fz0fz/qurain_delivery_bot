from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Qurain Delivery Bot is running ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    print("📥 نوع البيانات:", request.content_type)

    try:
        data = request.get_json(force=True)
        print("📥 البيانات المستلمة:", data)

        sender = data.get("from")
        message = data.get("body")

        print("👤 المرسل:", sender)
        print("💬 الرسالة:", message)

        if sender and message:
            reply = handle_message(message)
            send_whatsapp(sender, reply)

        return "OK", 200

    except Exception as e:
        print("❌ خطأ:", str(e))
        return "Error", 400

def handle_message(message):
    message = message.strip().lower()

    if message in ['0', '.', '٠', 'صفر', 'خدمات']:
        return """
*📋 القائمة الرئيسية لخدمات القرين:*

1️⃣ حكومي
2️⃣ صيدلية 💊
3️⃣ بقالة 🥤
4️⃣ خضار 🥬
5️⃣ رحلات ⛺️
6️⃣ حلا 🍮
7️⃣ أسر منتجة 🥧
8️⃣ مطاعم 🍔
9️⃣ قرطاسية 📗
🔟 محلات 🏪
11. شالية 🏖
12. وايت 🚛
13. شيول 🚜
14. دفان 🏗
15. مواد بناء وعوازل 🧱
16. عمال 👷
17. محلات مهنية 🔨
18. ذبائح وملاحم 🥩
19. نقل مدرسي ومشاوير 🚍
20. طلباتك
"""
    
    elif message == '2':
        return """
*[2]* *قائمة الصيدليات:*  
1- صيدلية ركن أطلس (القرين)  
2- صيدلية دواء البدر (الدليمية)  
3- صيدلية ساير (الدليمية)  

*99 - اطلب:* ستجد طلباتك في رقم 20 من القائمة الرئيسية.
"""
    
    elif message == '99':
        return "📥 أرسل طلبك بالتفصيل وسيتم حفظه للعرض لاحقاً في '20. طلباتك'."

    else:
        return f"📩 تم استلام رسالتك: {message}"

def send_whatsapp(to, message):
    url = "https://api.ultramsg.com/instance130542/messages/chat"
    payload = {
        "token": "9dxefhg0k4l3b7ak",
        "to": to,
        "body": message
    }
    response = requests.post(url, data=payload)
    print("📤 الرد على:", to, "✅" if response.ok else "❌", response.text)
