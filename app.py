from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message  # تأكد من الاستيراد هنا
import menu_app  # إذا كنت تحتاجه في مكان آخر

app = Flask(__name__)

# تخزين حالة كل مستخدم وطلباته
user_states = {}
user_orders = {}

@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if not data:
        return "❌ No data received", 400

    # إذا كان هذا اختبار Webhook من WaSenderAPI
    if data.get("event") == "webhook.test":
        print("📩 Received test webhook:", data)
        return {"status": "test ok"}, 200

    payload = data.get("data", {})

    user_id = payload.get("from")
    message = payload.get("body")
    driver_id = None
    latitude = None
    longitude = None

    # إذا كانت الرسالة من نوع "location" استخرج الإحداثيات من مفتاح location
    if payload.get("type") == "location":
        location = payload.get("location", {})
        if location:
            latitude = location.get("latitude")
            longitude = location.get("longitude")
    else:
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

    if not user_id or not message:
        return "❌ Missing fields", 400

    # إذا كانت الرسالة تحتوي على "قبول" اعتبرها قبول من المندوب
    if "قبول" in message:
        driver_id = user_id

    response = dispatch_message(
        user_id=user_id,
        message=message,
        user_states=user_states,
        user_orders=user_orders,
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude
    )

    # إرسال الرد إذا موجود
    if response:
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        send_message(phone, response)

    return "✅ OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
