from flask import Flask, request, jsonify
from dispatcher import dispatch_message
from send_utils import send_message
from workers_register import init_workers_table
import json, sys, traceback

init_workers_table()

app = Flask(__name__)

# حالتا المستخدم والطلبات (ذاكرة)
user_states = {}
user_orders = {}

AR_NUM_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def normalize_digits(s: str) -> str:
    if not isinstance(s, str):
        return s
    return s.translate(AR_NUM_MAP)

def log(msg):
    print(msg, flush=True)

def safe_get_json():
    try:
        return request.get_json(silent=True)
    except Exception as e:
        log(f"[JSON_ERROR] {e}")
        return None

def extract_from_baileys_payload(raw: dict):
    """
    يحاول استخراج user_id, text, latitude, longitude من شكل Baileys:
    {
      "messages": {
         "key": {"remoteJid": "...", "fromMe": false, ...},
         "message": {
             "conversation": "...",
             "extendedTextMessage": {"text": "..."},
             "locationMessage": {...}
         }
      }
    }
    يعيد tuple (user_id, text, lat, lng, from_me) أو (None,None,None,None,None) إذا غير صالح.
    """
    try:
        messages_obj = raw.get("messages")
        if not isinstance(messages_obj, dict):
            return None, None, None, None, None
        key = messages_obj.get("key", {})
        from_me = key.get("fromMe")
        remote_jid = key.get("remoteJid")
        msg_block = messages_obj.get("message", {})
        text = None
        lat = lng = None

        # نصوص محتملة
        if "conversation" in msg_block:
            text = msg_block["conversation"]
        elif "extendedTextMessage" in msg_block:
            text = msg_block["extendedTextMessage"].get("text")
        elif "ephemeralMessage" in msg_block:
            # أحياناً يكون النص داخل ephemeralMessage.message
            inner = msg_block["ephemeralMessage"].get("message", {})
            if "conversation" in inner:
                text = inner["conversation"]
            elif "extendedTextMessage" in inner:
                text = inner["extendedTextMessage"].get("text")

        # موقع
        loc = None
        if "locationMessage" in msg_block:
            loc = msg_block["locationMessage"]
        elif "ephemeralMessage" in msg_block:
            inner = msg_block["ephemeralMessage"].get("message", {})
            if "locationMessage" in inner:
                loc = inner["locationMessage"]

        if loc:
            lat = loc.get("degreesLatitude")
            lng = loc.get("degreesLongitude")

        return remote_jid, text, lat, lng, from_me
    except Exception as e:
        log(f"[EXTRACT_BAILEYS_ERROR] {e}")
        return None, None, None, None, None

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = safe_get_json()
    if data is None:
        log("[WARN] Non-JSON body")
        return jsonify({"ok": False, "ignored": "non_json"}), 200

    # دعم شكل سابق: {"data": {...}} أو الشكل المسطح
    payload = data.get("data") if isinstance(data.get("data"), dict) else data

    user_id = None
    message = None
    latitude = None
    longitude = None
    from_me = False

    # أولاً: حاول القراءة بطريقة "قديمه" (from/body)
    user_id = (
        payload.get("from")
        if isinstance(payload, dict) else None
    )
    message = (
        payload.get("body") if isinstance(payload, dict) else None
    )
    msg_type = payload.get("type") if isinstance(payload, dict) else None

    # إذا لم نجد user_id أو نص، جرّب شكل Baileys
    if not user_id and "messages" in payload:
        user_id, msg_baileys, lat_b, lng_b, from_me = extract_from_baileys_payload(payload)
        if msg_baileys is not None:
            message = msg_baileys
        if lat_b is not None:
            latitude = lat_b
        if lng_b is not None:
            longitude = lng_b
        # نوع الرسالة (اختياري)
        if msg_type is None and isinstance(payload.get("messages"), dict):
            # لا يوجد حقل نوع واضح، نتركه None
            pass

    # تجاهل رسائل البوت نفسه
    if from_me:
        return jsonify({"ok": True, "ignored": "from_me"}), 200

    # استخراج موقع في النمط القديم
    if msg_type == "location" and latitude is None and longitude is None:
        loc_obj = payload.get("location", {})
        latitude = loc_obj.get("latitude")
        longitude = loc_obj.get("longitude")
    else:
        # fallback لو أرسلت الحقول مباشرة
        if latitude is None:
            latitude = payload.get("latitude")
        if longitude is None:
            longitude = payload.get("longitude")

    # إذا لا يوجد user_id نهائياً
    if not user_id:
        log(f"[IGNORE] payload بدون user_id: {json.dumps(payload, ensure_ascii=False)[:400]}")
        return jsonify({"ok": True, "ignored": "no_user_id"}), 200

    # تطبيع الأرقام العربية داخل النص (إن وُجد)
    if isinstance(message, str):
        message = normalize_digits(message)

    # إذا لا يوجد نص ولا موقع → احتمل أنه حدث نظامي
    if (message is None or message.strip() == "") and not (latitude and longitude):
        return jsonify({"ok": True, "ignored": "empty"}), 200

    # منطق اعتبار السائق (قبول)
    driver_id = None
    if isinstance(message, str) and "قبول" in message:
        driver_id = user_id

    # استدعاء الديسباتشر
    try:
        response = dispatch_message(
            user_id=user_id,
            message=message or "",
            user_states=user_states,
            user_orders=user_orders,
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude
        )
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({"ok": False, "error": "dispatch_error", "detail": str(e)[:200]}), 500

    # إرسال الرد إن وجد
    if response:
        try:
            phone = user_id.split("@")[0] if "@s.whatsapp.net" in user_id or "@c.us" in user_id else user_id
            send_message(phone, response)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)

    return jsonify({"ok": True}), 200

import menu_app  # إبقِه إذا كنت تحتاجه
