from flask import Flask, request, jsonify
from dispatcher import dispatch_message
from send_utils import send_message  # تأكد من وجوده

app = Flask(__name__)

# بيانات المستخدمين والطلبات
user_states = {}
user_orders = {}

# صفحة اختبارية للتأكد من أن السيرفر شغال
@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!", 200

# Webhook لاستقبال الرسائل
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)  # force=True لضمان قراءة JSON
    except Exception as e:
        print("❌ Error parsing JSON:", e)
        return "Invalid JSON", 400

    if not data:
        print("❌ No data received")
        return "No data", 400

    # اختبار Webhook من WaSenderAPI
    if data.get("event") == "webhook.test":
        print("📩 Received test webhook:", data)
        return jsonify({"status": "test ok"}), 200

    payload = data.get("data", {})

    user_id = payload.get("from")
    message = payload.get("body")
    driver_id = None
    latitude = None
    longitude = None

    # إذا كانت الرسالة من نوع "location" استخرج الإحداثيات
    if payload.get("type") == "location":
        location = payload.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")
    else:
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

    if not user_id or not message:
        print("❌ Missing user_id or message")
        return "Missing fields", 400

    # معالجة قبول المندوب للطلب
    if "قبول" in message:
        driver_id = user_id

    # إرسال الرسالة إلى ديسباتشر
    response = dispatch_message(
        user_id=user_id,
        message=message,
        user_states=user_states,
        user_orders=user_orders,
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude
    )

    # إذا فيه رد نرسله للمستخدم
    if response:
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        send_message(phone, response)

    print(f"✅ Processed message from {user_id}: {message}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
