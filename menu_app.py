from flask import render_template, request
import requests
import os

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

    # إعداد الرسالة
    text = f"📦 *طلب جديد من المتجر:*\n- " + "\n- ".join(items)

    # جلب بيانات UltraMsg من متغيرات البيئة
    ultra_token = os.getenv("ULTRA_TOKEN")
    instance_id = os.getenv("INSTANCE_ID")

    if not ultra_token or not instance_id:
        return "❌ متغيرات البيئة ULTRA_TOKEN أو INSTANCE_ID غير معرفة"

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "token": ultra_token,
        "to": phone,
        "body": text
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return "✅ تم إرسال الطلب إلى واتساب!"
        else:
            return f"❌ فشل في الإرسال: {response.text}"
    except Exception as e:
        return f"❌ خطأ أثناء الاتصال بـ UltraMsg: {str(e)}"