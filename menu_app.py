from flask import render_template, request
import requests

from app import app  # استدعاء app من ملفك الرئيسي

@app.route("/menu", methods=["GET"])
def menu_page():
    return render_template("menu.html")


@app.route("/send_menu_order", methods=["POST"])
def send_menu_order():
    phone = request.form.get("phone")
    items = request.form.getlist("items")

    if not phone or not items:
        return "❗ يجب إدخال رقم الهاتف واختيار منتج واحد على الأقل"

    # الرسالة للتجربة، مع وسم واضح
    text = f"📦 [منيو HTML]\n- " + "\n- ".join(items)

    # بيانات UltraMsg (مكشوفة للتجربة فقط)
    ultra_token = "9dxefhg0k4l3b7ak"
    instance_id = "instance130542"

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "token": ultra_token,
        "to": phone,
        "body": text
    }

    try:
        response = requests.post(url, json=payload)

        # 🪵 طباعة للتتبع في لوق Render
        print("📨 تم إرسال الطلب إلى UltraMsg")
        print("📤 UltraMsg response:", response.status_code, response.text)

        if response.status_code == 200:
            return "✅ تم إرسال الطلب إلى واتساب!"
        else:
            return f"❌ فشل في الإرسال: {response.text}"
    except Exception as e:
        print("❌ خطأ في الاتصال بـ UltraMsg:", str(e))
        return f"❌ خطأ أثناء الاتصال بـ UltraMsg: {str(e)}"