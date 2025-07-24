import os
from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message

# متغيرات لحفظ حالة المستخدم والطلبات
user_states = {}
user_orders = {}

# استيراد قائمة المناديب
from mandoubs import mandoubs

app = Flask(__name__)

def is_mandoub(user_id):
    return any(m["id"] == user_id for m in mandoubs)

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

    # ✅ تمييز إذا كان المرسل مندوب أو عميل
    if is_mandoub(user_id):
        response = dispatch_message(user_id, message, user_states, user_orders, driver_id=user_id)
    else:
        response = dispatch_message(user_id, message, user_states, user_orders)

    if response:
        send_message(user_id, response)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
