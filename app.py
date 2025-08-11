from flask import Flask, request, jsonify
from dispatcher import dispatch_message
from send_utils import send_message
from workers_register import init_workers_table
import json
import sys
import traceback

init_workers_table()

app = Flask(__name__)

user_states = {}
user_orders = {}

def log(msg):
    print(msg, flush=True)

def safe_get_json():
    try:
        data = request.get_json(silent=True)
        return data
    except Exception as e:
        log(f"[JSON_ERROR] {e}")
        return None

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = safe_get_json()
    if data is None:
        log("[WARN] Non-JSON / empty body")
        return jsonify({"ok": False, "error": "invalid_json"}), 200  # لا نعيد 400 حتى لا يعاد الإرسال بلا فائدة

    # بعض المنصات ترسل مباشرة بدون التغليف داخل data
    # لديك سابقاً payload = data.get("data", {})
    # نجرب الدمج:
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    if payload is None:
        payload = {}

    # استخرج الحقول المرنة
    user_id = (
        payload.get("from") or
        payload.get("sender") or
        payload.get("jid")
    )

    # النص يمكن أن يوجد في body أو text أو message
    message = (
        payload.get("body") or
        payload.get("text") or
        payload.get("message")
    )

    msg_type = payload.get("type") or payload.get("event")
    latitude = None
    longitude = None

    # استخراج الموقع
    if msg_type == "location":
        loc = payload.get("location") or {}
        latitude = loc.get("latitude")
        longitude = loc.get("longitude")
    else:
        # أحياناً يرسل الوسيط الحقول مباشرة
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

    # إذا لا يوجد مرسل -> لا يمكن المعالجة
    if not user_id:
        log(f"[IGNORE] payload بدون user_id: {json.dumps(payload, ensure_ascii=False)[:400]}")
        return jsonify({"ok": True, "ignored": "no_user_id"}), 200

    # إذا لا يوجد رسالة نصية ولا موقع ولا شيء قابل للاستخدام -> ربما حدث حالة (status / ack)
    if message is None or str(message).strip() == "":
        # أحداث النظام: لا تعيد 400
        if msg_type in ("ack", "status", "delivery", "presence", "read", "reaction"):
            return jsonify({"ok": True, "ignored": msg_type}), 200
        # إذا موقع بدون body (منطقي)
        if msg_type == "location" and latitude and longitude:
            # مرر للـ dispatcher برسالة افتراضية فارغة (قد يستقبل shops أو طلبات سائق)
            response = dispatch_message(
                user_id=user_id,
                message="",   # فارغ
                user_states=user_states,
                user_orders=user_orders,
                driver_id=None,
                latitude=latitude,
                longitude=longitude
            )
            # عادةً shops_service أو المنطق الآخر سيرجع رد
            if response:
                phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
                send_message(phone, response)
            return jsonify({"ok": True, "handled": "location_no_text"}), 200

        # لا يوجد نص ولا موقع صالح: تجاهل
        log(f"[IGNORE] Empty message for user {user_id}: {json.dumps(payload, ensure_ascii=False)[:400]}")
        return jsonify({"ok": True, "ignored": "empty"}), 200

    # تحديد هل رسالة قبول (سائق)
    driver_id = None
    if "قبول" in str(message):
        driver_id = user_id

    # نفذ المنطق
    try:
        response = dispatch_message(
            user_id=user_id,
            message=str(message),
            user_states=user_states,
            user_orders=user_orders,
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude
        )
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"ok": False, "error": "dispatch_error", "detail": str(e)[:200]}), 500

    # إرسال الرد إن وُجد
    if response:
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        try:
            send_message(phone, response)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)

    return jsonify({"ok": True}), 200

import menu_app  # إذا تحتاجه
