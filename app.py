import os
from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message
from mandoubs import mandoubs

user_states = {}
user_orders = {}

def is_mandoub(user_id):
    return any(m["id"] == user_id for m in mandoubs)

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("📨 البيانات المستلمة من UltraMsg:")
    print(data)
    msg_data = data.get("data", {})
    message = msg_data.get("body", "").strip()
    user_id = msg_data.get("from", "").strip()
    # التقاط الموقع إذا وُجد
    latitude = msg_data.get("latitude")
    longitude = msg_data.get("longitude")
    if not message and not (latitude and longitude) or not user_id:
        print("❌ تم استلام بيانات غير صالحة")
        return "Invalid", 400
    # تمرير الإحداثيات إن وجدت
    if is_mandoub(user_id):
        response = dispatch_message(user_id, message, user_states, user_orders, driver_id=user_id, latitude=latitude, longitude=longitude)
    else:
        response = dispatch_message(user_id, message, user_states, user_orders, latitude=latitude, longitude=longitude)
    if response:
        send_message(user_id, response)
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
