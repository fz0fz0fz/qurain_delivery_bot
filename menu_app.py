from flask import render_template, request
from app import app
from send_utils import send_message

@app.route("/menu", methods=["GET"])
def show_menu():
    return render_template("menu.html")

@app.route("/send_menu_order", methods=["POST"])
def send_menu_order():
    name = request.form.get("name")
    phone = request.form.get("phone")
    items = request.form.getlist("items")

    if not phone or not items:
        return "❗ يجب إدخال رقم الهاتف واختيار منتج واحد على الأقل"

    message = f"*📦 [طلب من الموقع]*\n👤 الاسم: {name}\n📞 رقم العميل: {phone}\n🛒 الطلب:\n- " + "\n- ".join(items)

    send_message("966503813344", message)
    send_message("966507005272", message)

    return "✅ تم إرسال الطلب عبر واتساب!"
