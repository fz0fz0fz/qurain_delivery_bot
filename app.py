from flask import Flask, request, jsonify

app = Flask(__name__)

# صفحة اختبارية للتأكد إن السيرفر شغال
@app.route("/")
def index():
    return "Service is live!", 200

# Webhook لاستقبال الرسائل
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)  # force=True عشان يجبر flask يقرأ JSON
    except Exception as e:
        print("Error parsing JSON:", e)
        return "Invalid JSON", 400

    if not data:
        print("No data received")
        return "No data", 400

    # مثال: طباعة البيانات اللي وصلت
    print("Received webhook data:", data)

    # هنا ممكن تضيف أي منطق للرد أو التعامل مع الرسائل
    # مثلاً: إرسال الرد للبوت أو حفظها في ملف/قاعدة بيانات

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
