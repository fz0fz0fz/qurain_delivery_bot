from flask import render_template, request
import requests

from app import app  # ✅ استدعاء التطبيق الرئيسي من app.py

@app.route("/menu", methods=["GET"])
def menu_page():
    return render_template("menu.html")


@app.route("/send_menu_order", methods=["POST"])
def send_menu_order():
    items = request.form.getlist("items")
    if not items:
        return "❗ يجب اختيار منتج واحد على الأقل"

    # نص الرسالة الموحد
    text = f"📦 [منيو HTML - اختبار متعدد]\n- " + "\n- ".join(items)

    # بيانات UltraMsg
    ultra_token = "9dxefhg0k4l3b7ak"
    instance_id = "instance130542"
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"

    # ✅ قائمة الأرقام للتجربة
    test_numbers = [
        "966503813344",  # رقمك الأساسي (كعميل)
        "966507005272",  # رقم البوت (instance)
        "9665XXXXXXX"    # ← عدّل هذا لرقم آخر تبي تختبر عليه
    ]

    for phone in test_numbers:
        payload = {
            "token": ultra_token,
            "to": phone,
            "body": text
        }

        try:
            response = requests.post(url, json=payload)
            print(f"📤 إرسال إلى {phone} → {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ خطأ عند الإرسال إلى {phone}: {str(e)}")

    return "✅ تم إرسال الرسالة إلى جميع الأرقام للتجربة"