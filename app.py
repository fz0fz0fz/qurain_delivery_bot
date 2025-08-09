from flask import Flask, request, jsonify
from dispatcher import dispatch_message
from send_utils import send_message

app = Flask(__name__)

user_states = {}
user_orders = {}

@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    # اطبع لمرة الاختبار، ثم احذفه لاحقًا
    app.logger.info("Webhook body: %s", data)

    # 1) حمل الحمولة المرنة
    payload = data.get("data") or data

    # لو كان events من نوع messages.upsert قد تحتوي مصفوفة
    msg = payload.get("message")
    if not msg and isinstance(payload.get("messages"), list) and payload["messages"]:
        msg = payload["messages"][0]

    # 2) استخرج المرسل
    user_id = (
        (payload.get("from") or payload.get("jid") or payload.get("sender")) or
        (msg.get("from") if isinstance(msg, dict) else None) or
        (msg.get("jid") if isinstance(msg, dict) else None) or
        (msg.get("sender") if isinstance(msg, dict) else None)
    )

    # 3) استخرج النص
    message = (
        payload.get("body") or payload.get("text") or
        (msg.get("body") if isinstance(msg, dict) else None) or
        (msg.get("text") if isinstance(msg, dict) else None) or
        (msg.get("message") if isinstance(msg, dict) else None)
    )

    # 4) استخرج الموقع (إن وجد)
    location = (
        payload.get("location") or
        (msg.get("location") if isinstance(msg, dict) else None)
    )
    latitude = None
    longitude = None
    if isinstance(location, dict):
        latitude = location.get("latitude")
        longitude = location.get("longitude")

    # لو ما في مرسل، اكتفِ بـ 200
    if not user_id:
        return jsonify({"ok": True, "note": "no user_id"}), 200

    # 5) حدّد إن كانت رسالة قبول سائق
    driver_id = user_id if (message and "قبول" in message) else None

    # 6) استدعِ منطقك
    response = None
    if message or (latitude and longitude):
        response = dispatch_message(
            user_id=user_id,
            message=message or "",   # مرر نصًا فارغًا لوكيشن بدون نص
            user_states=user_states,
            user_orders=user_orders,
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude
        )

    # 7) أرسل الرد إن وُجد
    if response:
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        try:
            send_message(to=phone, text=response)
        except Exception as e:
            app.logger.exception("send_message failed: %s", e)

    return jsonify({"ok": True}), 200

import menu_app  # ابقه لو تحتاجه