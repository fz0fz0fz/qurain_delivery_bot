from flask import Flask, request, jsonify
from dispatcher import dispatch_message
from send_utils import send_message
from workers_register import init_workers_table
import json, sys, traceback, time

init_workers_table()

app = Flask(__name__)

user_states = {}
user_orders = {}

# تخزين معرفات الرسائل المعالجة (في الذاكرة)
# البنية: { message_id: timestamp }
processed_message_ids = {}
DEDUP_TTL_SECONDS = 3600  # ساعة (يمكن تخفيضه)

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

def cleanup_processed():
    """تنظيف المعرفات القديمة لتفادي تراكم الذاكرة."""
    now = time.time()
    to_delete = [mid for mid, ts in processed_message_ids.items() if now - ts > DEDUP_TTL_SECONDS]
    for mid in to_delete:
        processed_message_ids.pop(mid, None)

def extract_from_baileys_payload(raw: dict):
    """
    استخراج user_id, text, lat, lng, from_me, message_id من بنية Baileys.
    """
    try:
        messages_obj = raw.get("messages")
        if not isinstance(messages_obj, dict):
            return None, None, None, None, None, None
        key = messages_obj.get("key", {})
        from_me = key.get("fromMe")
        remote_jid = key.get("remoteJid")
        message_id = key.get("id")
        msg_block = messages_obj.get("message", {})
        text = None
        lat = lng = None

        # نصوص محتملة
        if "conversation" in msg_block:
            text = msg_block["conversation"]
        elif "extendedTextMessage" in msg_block:
            text = msg_block["extendedTextMessage"].get("text")
        elif "ephemeralMessage" in msg_block:
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

        return remote_jid, text, lat, lng, from_me, message_id
    except Exception as e:
        log(f"[EXTRACT_BAILEYS_ERROR] {e}")
        return None, None, None, None, None, None

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = safe_get_json()
    if data is None:
        log("[WARN] Non-JSON body")
        return jsonify({"ok": False, "ignored": "non_json"}), 200

    payload = data.get("data") if isinstance(data.get("data"), dict) else data

    user_id = None
    message = None
    latitude = None
    longitude = None
    from_me = False
    message_id = None

    # شكل سابق (from/body)
    if isinstance(payload, dict):
        user_id = payload.get("from")
        message = payload.get("body")
        msg_type = payload.get("type")
    else:
        msg_type = None

    # شكل Baileys
    if (not user_id or not message) and isinstance(payload, dict) and "messages" in payload:
        user_id_b, text_b, lat_b, lng_b, from_me_b, msg_id_b = extract_from_baileys_payload(payload)
        if user_id_b:
            user_id = user_id_b
        if text_b is not None:
            message = text_b
        if lat_b is not None:
            latitude = lat_b
        if lng_b is not None:
            longitude = lng_b
        if from_me_b is not None:
            from_me = from_me_b
        if msg_id_b:
            message_id = msg_id_b

    # استخلاص الموقع (نمط قديم)
    if msg_type == "location" and latitude is None and longitude is None:
        loc_obj = payload.get("location", {})
        latitude = loc_obj.get("latitude")
        longitude = loc_obj.get("longitude")
    else:
        if latitude is None:
            latitude = payload.get("latitude")
        if longitude is None:
            longitude = payload.get("longitude")

    # تجاهل رسائل البوت نفسه
    if from_me:
        return jsonify({"ok": True, "ignored": "from_me"}), 200

    # تنظيف دوري للذاكرة
    cleanup_processed()

    # تطبيع أرقام عربية في النص
    if isinstance(message, str):
        message = normalize_digits(message)

    # Dedup: إذا لدينا message_id نستعمله
    if message_id:
        if message_id in processed_message_ids:
            # تم الرد سابقاً
            return jsonify({"ok": True, "ignored": "duplicate"}), 200
        processed_message_ids[message_id] = time.time()

    # التحقق من وجود user_id
    if not user_id:
        log(f"[IGNORE] no user_id: {json.dumps(payload, ensure_ascii=False)[:300]}")
        return jsonify({"ok": True, "ignored": "no_user_id"}), 200

    # إذا لا نص ولا موقع
    if (not message or message.strip() == "") and not (latitude and longitude):
        return jsonify({"ok": True, "ignored": "empty"}), 200

    # تحديد السائق
    driver_id = None
    if isinstance(message, str) and "قبول" in message:
        driver_id = user_id

    # استدعاء المنطق
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

    if response:
        try:
            # تحويل remoteJid مثل 9665xxxx@s.whatsapp.net إلى رقم فقط
            phone = user_id.split("@")[0] if "@s.whatsapp.net" in user_id or "@c.us" in user_id else user_id
            send_message(phone, response)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)

    return jsonify({"ok": True}), 200

import menu_app  # إذا مطلوب
