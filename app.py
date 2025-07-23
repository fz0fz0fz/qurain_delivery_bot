import os
from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message

# متغيرات لحفظ حالة المستخدم والطلبات
user_states = {}
user_orders = {}

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("📨 البيانات المستلمة من UltraMsg:")
    print(data)

    msg_data = data.get("data", {})
    message = msg_data.get("body", "").strip()
    user_id = msg_data.get("from", "").strip()

    if not message or not user_id:
        print("❌ تم استلام بيانات غير صالحة")
        return "Invalid", 400

    # ✅ استدعاء الدالة الرئيسية وتمرير البيانات اللازمة
    response = dispatch_message(user_id, message, user_states, user_orders)

    if response:
        send_message(user_id, response)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
