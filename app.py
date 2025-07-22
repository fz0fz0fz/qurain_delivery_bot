from flask import Flask, request, jsonify
from dispatcher import dispatch_message

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "data" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    payload = data["data"]
    phone = payload.get("from")
    message = payload.get("body", "").strip()

    if not phone or not message:
        return jsonify({"error": "Missing phone or message"}), 400

    dispatch_message(message, phone)
    return jsonify({"status": "ok"})
