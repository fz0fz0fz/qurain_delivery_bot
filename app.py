from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message  # تأكد من وجودها

app = Flask(__name__)

user_states = {}
user_orders = {}

@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print("Error parsing JSON:", e)
        return "Invalid JSON", 400

    print("Received data:", data)  # يظهر البيانات في السجل

    if not data:
        print("No data received")
        return "No data", 400

    # اختبار الويب هوك
    if data.get("event") == "webhook.test":
        print("📩 Received test webhook:", data)
        return {"status": "test ok"}, 200

    payload = data.get("data") or data

    # استخراج الرسائل من البيانات
    messages = payload.get("messages")
    if not messages:
        print("❌ No messages object found")
        return "No messages object", 400

    key = messages.get("key", {})
    user_id = key.get("remoteJid")
    from_me = key.get("fromMe", False)  # هل الرسالة من البوت نفسه؟

    # استخراج نص الرسالة
    message_obj = messages.get("message", {})
    message = message_obj.get("conversation", "")

    # تجاهل الرسائل التي أرسلها البوت نفسه لمنع الحلقة اللانهائية
    if from_me:
        print("🔄 رسالة من البوت نفسه، تم تجاهلها")
        return "Message from bot - ignored", 200

    driver_id = None
    latitude = None
    longitude = None

    # لو تريد دعم الموقع، أضف هنا حسب شكل بياناتك لاحقًا
    # if message_obj.get("type") == "location":
    #     location = message_obj.get("location", {})
    #     latitude = location.get("latitude")
    #     longitude = location.get("longitude")

    if not user_id:
        print("❌ Missing user_id")
        return "Missing user_id", 400

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

    if response:
        phone = user_id.split("@")[0] if "@" in user_id else user_id
        send_message(phone, response)

    return "✅ OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
