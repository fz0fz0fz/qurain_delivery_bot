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

    print("Received data:", data)  # تأكد أن هذا السطر داخل الدالة

    if not data:
        print("No data received")
        return "No data", 400

    if data.get("event") == "webhook.test":
        print("📩 Received test webhook:", data)
        return {"status": "test ok"}, 200

    payload = data.get("data") or data

    # هنا التعديل
    user_id = payload.get("from") or payload.get("sender") or payload.get("chatId") or payload.get("user") or None
    message = payload.get("body") or payload.get("message") or ""  # لو مافي نص خليها فارغة
    driver_id = None
    latitude = None
    longitude = None

    if payload.get("type") == "location":
        location = payload.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")
    else:
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

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
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        send_message(phone, response)

    return "✅ OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
