@app.route("/send_menu_order", methods=["POST"])
def send_menu_order():
    # الرسالة المختارة
    items = request.form.getlist("items")
    if not items:
        return "❗ يجب اختيار منتج واحد على الأقل"

    text = f"📦 [منيو HTML - اختبار متعدد]\n- " + "\n- ".join(items)

    ultra_token = "9dxefhg0k4l3b7ak"
    instance_id = "instance130542"
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"

    # 🔁 قائمة الأرقام للتجربة
    test_numbers = [
        "966503813344",  # رقمك (جوال)
        "966507005272",  # رقم البوت
        "966506107151"    # ← عدّل هذا إلى رقم ثالث تجرب عليه
    ]

    # 🔄 أرسل الرسالة لكل رقم في القائمة
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