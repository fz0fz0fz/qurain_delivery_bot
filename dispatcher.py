from send_utils import send_message, generate_order_id
from order_logger import save_order
from services.unified_service import handle_service

# ==== المتغيرات الجديدة لإدارة الطلبات (ضعها في مكان مناسب GLOBAL) ====
order_to_user = {}     # order_id -> user_id
order_to_driver = {}   # order_id -> driver_id

# عرض القائمة الرئيسية عند إرسال "0" أو "." أو "٠" أو "خدمات"
def handle_main_menu(message):
    if message.strip() in ["0", ".", "٠", "خدمات"]:
        return (
            "*📋 خدمات القرين:*\n"
            "1️⃣ حكومي\n"
            "2️⃣ صيدلية 💊\n"
            "3️⃣ بقالة 🥤\n"
            "4️⃣ خضار 🥬\n"
            "5️⃣ رحلات ⛺️\n"
            "6️⃣ حلا 🍮\n"
            "7️⃣ أسر منتجة 🥧\n"
            "8️⃣ مطاعم 🍔\n"
            "9️⃣ قرطاسية 📗\n"
            "🔟 محلات 🏪\n"
            "11. شالية 🏖\n"
            "12. وايت 🚛\n"
            "13. شيول 🚜\n"
            "14. دفان 🏗\n"
            "15. مواد بناء وعوازل 🧱\n"
            "16. عمال 👷\n"
            "17. محلات مهنية 🔨\n"
            "18. ذبائح وملاحم 🥩\n"
            "19. نقل مدرسي ومشاوير 🚍\n"
            "20. طلباتك 🧾\n\n"
            "✉️ لاقتراح أو شكوى أرسل: 100"
        )
    return None

# معالجة الشكاوى أو الاقتراحات (بدون تعديل)
def handle_feedback(user_id, message, user_states):
    if message.strip() == "100":
        user_states[user_id] = "awaiting_feedback"
        return "✉️ أرسل الآن رسالتك (اقتراح أو شكوى)"

    elif user_states.get(user_id) == "awaiting_feedback":
        user_states.pop(user_id, None)
        send_message("966503813344", f"💬 شكوى من {user_id}:\n{message}")
        return "✅ تم استلام رسالتك، شكرًا لك."

    return None

# عرض الطلبات السابقة (بدون تعديل)
def handle_view_orders(user_id, message, user_orders):
    if message.strip() == "20":
        orders = user_orders.get(user_id, {})
        if not orders:
            return "📭 لا توجد طلبات محفوظة حتى الآن."
        
        response = "*🗂 طلباتك المحفوظة:*\n"
        for service, order in orders.items():
            response += f"\n📌 *{service}:*\n- {order}"
        response += "\n\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
        return response
    return None

# ============= دالة إنهاء الطلبات (معدلة حسب المطلوب) =============
def handle_finalize_order(user_id, message, user_orders):
    if message.strip() != "تم":
        return None

    orders = user_orders.get(user_id)
    if not orders:
        return "❗️لا توجد طلبات لإرسالها."

    order_id = generate_order_id()
    summary = f"*🆔 رقم الطلب: {order_id}*\n"
    for service, order in orders.items():
        summary += f"\n📦 *{service}:*\n- {order}"

    save_order(order_id, user_id, orders)
    
    # ==== سجل علاقة الطلب ====
    order_to_user[order_id] = user_id

    # === الجديد: إرسال الطلب للمناديب فقط (إن وجد) ===
    try:
        from mandoubs import mandoubs
        for m in mandoubs:
            send_message(m["id"], f"📦 طلب جديد من {user_id}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")
    except ImportError:
        # إذا لم يوجد ملف mandoubs.py أو قائمة مناديب، أرسل للقروب أو مندوب افتراضي
        send_message("966503813344", f"📦 طلب جديد من {user_id}:\n\n{summary}\n\nللقبول أرسل: قبول {order_id}")

    # === (اختياري) إذا لازلت تريد إرسال الطلب للمحلات (vendors) أبقه:
    for service, order in orders.items():
        vendor_msg = f"*طلب جديد - {service}*\nرقم الطلب: {order_id}\n- {order}"
        send_message("966503813344", vendor_msg)

    # حذف الطلبات بعد الإرسال
    user_orders.pop(user_id, None)

    # === الجديد: إبلاغ العميل بانتظار قبول مندوب ===
    msg = f"✅ تم تسجيل طلبك برقم *{order_id}*، بانتظار قبول مندوب. سيتم التواصل معك قريبًا."
    send_message(user_id, msg)
    return None

# ==== دالة جديدة: معالجة قبول الطلب من المندوب ====
def handle_driver_accept_order(message, driver_id, user_states):
    # مثال على رسالة القبول: "قبول G124"
    if message.strip().startswith("قبول "):
        order_id = message.strip().split(" ", 1)[1]
        user_id = order_to_user.get(order_id)
        if user_id:
            order_to_driver[order_id] = driver_id
            user_states[user_id] = "awaiting_location"
            send_message(user_id, f"🚗 تم قبول طلبك (رقم {order_id}) من قبل المندوب. الرجاء إرسال موقعك الآن.")
            send_message(driver_id, f"✅ تم تسجيل قبولك للطلب رقم {order_id}. انتظر موقع العميل.")
            return "تمت معالجة قبول الطلب."
        else:
            send_message(driver_id, "🚫 لم يتم العثور على هذا الرقم.")
            return "لم يتم العثور على الطلب."
    return None

# ==== دالة جديدة: استقبال الموقع من العميل وإرساله للمندوب ====
def handle_user_location(user_id, message, user_states):
    if user_states.get(user_id) == "awaiting_location":
        # ابحث عن رقم الطلب لهذا العميل
        order_id = None
        for oid, uid in order_to_user.items():
            if uid == user_id:
                order_id = oid
                break
        if not order_id:
            send_message(user_id, "🚫 لم يتم العثور على رقم طلبك.")
            return "لا يوجد طلب بانتظار موقع."
        driver_id = order_to_driver.get(order_id)
        if not driver_id:
            send_message(user_id, "🚫 لم يتم العثور على المندوب المرتبط بالطلب.")
            return "لا يوجد مندوب مرتبط بالطلب."
        # أرسل الموقع للمندوب
        send_message(driver_id, f"📍 موقع العميل للطلب رقم {order_id}: {message}")
        user_states.pop(user_id, None)
        send_message(user_id, "✅ تم إرسال موقعك للمندوب. شكرًا لك.")
        return "تم إرسال الموقع"
    return None

# =========================
# الدالة الرئيسية
def dispatch_message(user_id, message, user_states, user_orders, driver_id=None):
    # القائمة الرئيسية
    response = handle_main_menu(message)
    if response:
        return response

    # الشكاوى
    response = handle_feedback(user_id, message, user_states)
    if response:
        return response

    # عرض الطلبات
    response = handle_view_orders(user_id, message, user_orders)
    if response:
        return response

    # إنهاء الطلبات
    response = handle_finalize_order(user_id, message, user_orders)
    if response:
        return response

    # قبول الطلب من المندوب (لو كان هذا المستخدم مناديب)
    if driver_id:
        response = handle_driver_accept_order(message, driver_id, user_states)
        if response:
            return response

    # استقبال الموقع من العميل
    response = handle_user_location(user_id, message, user_states)
    if response:
        return response

    # الخدمات الموحدة مثل صيدلية، بقالة، خضار
    for service_id, service_info in {
        "2": {"name": "الصيدلية", "stores": ["صيدلية الدواء", "صيدلية النهدي"]},
        "3": {"name": "البقالة", "stores": ["بقالة التميمي", "بقالة الخير"]},
        "4": {"name": "الخضار", "stores": ["خضار الطازج", "سوق المزارعين"]},
    }.items():
        response = handle_service(
            user_id,
            message,
            user_states,
            user_orders,
            service_id,
            service_info["name"],
            service_info["stores"]
        )
        if response:
            return response

    return None  # لا يوجد رد مفهوم
