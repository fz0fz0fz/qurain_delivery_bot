from flask import render_template, request
import requests

from app import app  # استدعاء الـ app الرئيسي من app.py

@app.route("/menu", methods=["GET"])
def menu_page():
    return render_template("menu.html")


@app.route("/send_menu_order", methods=["POST"])
def send_menu_order():
    phone = request.form.get("phone")
    items = request.form.getlist("items")

    if not items:
        return "❗ يجب اختيار منتج واحد على الأقل"

    text = f"📦 *طلب جديد من المتجر:*\n- " + "\n- ".join(items)

    payload = {
        "token": "YOUR_TOKEN_HERE",      # ← استبدل
        "to": phone,
        "body": text
    }

    instance_id = "YOUR_INSTANCE_ID"     # ← استبدل
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return "✅ تم إرسال الطلب إلى واتساب!"
    else:
        return f"❌ حدث خطأ: {response.text}"