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

    print("Received data:", data)  # هنا يظهر البيانات المستقبلة في السجل

    if not data:
        print("No data received")
        return "No data", 400

    if data.get("event") == "webhook.test":
        print("📩 Received test webhook:", data)
        return {"status": "test ok"}, 200

    payload = data.get("data") or data

    # استخراج user_id من remoteJid داخل key
    try:
        messages = payload.get("messages")
        if not messages:
            print("❌ No messages object found")
            return "No messages object", 400

        key = messages.get("key")
        user_id = key.get("remoteJid")
        # استخراج الرسالة من conversation
        message_obj = messages.get("message", {})
        message = message_obj.get("conversation", "")
    except Exception as e:
        print("❌ Error extracting user_id and message:", e)
        return "Error extracting user_id/message", 400

    driver_id = None
    latitude = None
    longitude = None

    # لو الرسالة من نوع location (يمكنك تعديلها لاحقًا حسب الخدمة)
    if message_obj.get("type") == "location":
        location = message_obj.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")
    else:
        latitude = None
        longitude = None

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
