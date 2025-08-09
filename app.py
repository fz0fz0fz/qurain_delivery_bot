# app.py
import logging, threading
from flask import Flask, request, jsonify
from send_utils import send_message  # نفس التوقيع السابق

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def handle_event_async(payload):
    try:
        # مثال بسيط: لو حدث messages.upsert وفيه نص من المستخدم
        msg = (payload or {}).get("message") or {}
        frm = msg.get("from") or msg.get("jid")  # حسب بنية الحدث
        text = msg.get("text") or msg.get("body")

        if frm and text:
            # نادِ منطقك هنا (توجيه للقوائم/الخدمات…)
            reply = your_dispatch_function(frm, text)  # اكتبها عندك
            if reply:
                send_message(to=frm, text=reply)
    except Exception as e:
        app.logger.exception(f"Async handler error: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    # شغّل المعالجة بالخلفية
    threading.Thread(target=handle_event_async, args=(data,), daemon=True).start()
    # ردّ فوري
    return jsonify({"ok": True}), 200