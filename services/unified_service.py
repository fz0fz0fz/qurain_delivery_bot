import sqlite3
from datetime import datetime
from collections import defaultdict

def save_order(user_id, service_name, order_text):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO orders (user_id, service_name, order_text, created_at) VALUES (?, ?, ?, ?)',
        (user_id, service_name, order_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def get_orders_for_user(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT service_name, order_text, created_at FROM orders WHERE user_id=?', (user_id,))
    results = c.fetchall()
    conn.close()

    orders_by_service = defaultdict(list)
    for service, order, created_at in results:
        orders_by_service[service].append(f"- {order}\n🕒 {created_at}")

    response = "*🗂 طلباتك المحفوظة:*\n\n"
    for service, orders in orders_by_service.items():
        response += f"📌 *{service}:*\n" + "\n".join(orders) + "\n"

    response += "\nعند الانتهاء، أرسل كلمة *تم* لإرسال الطلب."
    return response

def handle_service(
    user_id,
    message,
    user_states,
    user_orders,
    service_id,
    service_name,
    stores_list,
    allowed_service_ids,
    main_menu_text=None  # القائمة الرئيسية يتم تمريرها من dispatcher.py
):
    msg = message.strip()
    current_state = user_states.get(user_id)
    
    # تحويل allowed_service_ids إلى dict إذا وصل كقائمة
    if isinstance(allowed_service_ids, list):
        allowed_service_ids = {str(idx+1): name for idx, name in enumerate(allowed_service_ids)}

    # إذا الحالة هي القائمة الرئيسية، لا تستقبل أي نص إلا رقم خدمة أو 0 أو 20
    if current_state == "main_menu":
        if msg == "0":
            return main_menu_text if main_menu_text else "القائمة الرئيسية غير متوفرة!"
        if msg == "20":
            return get_orders_for_user(user_id)
        if msg in allowed_service_ids:
            chosen_service = allowed_service_ids[msg]
            user_states[user_id] = f"awaiting_order_{chosen_service}"
            response = f"*📦 {chosen_service}:*\n"
            for i, store in enumerate(stores_list, 1):
                response += f"{i}. {store}\n"
            response += "\n99. اطلب الآن"
            return response
        # تجاهل أي نص آخر في القائمة الرئيسية
        return "❗️يرجى اختيار رقم خدمة من القائمة أولًا."

    # رجوع المستخدم للقائمة الرئيسية من أي مكان
    if msg == "0":
        user_states[user_id] = "main_menu"
        return main_menu_text if main_menu_text else "القائمة الرئيسية غير متوفرة!"

    # دخول المستخدم على خدمة معينة من القائمة (مثال: 2 أو 3 أو 4 ...)
    if msg in allowed_service_ids:
        chosen_service = allowed_service_ids[msg]
        user_states[user_id] = f"awaiting_order_{chosen_service}"
        response = f"*📦 {chosen_service}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # بدء إدخال الطلب بعد الضغط على 99 (فقط إذا الحالة صحيحة)
    if msg == "99":
        if current_state and current_state.startswith("awaiting_order_"):
            current_service = current_state.replace("awaiting_order_", "")
            user_states[user_id] = f"waiting_input_{current_service}"
            return f"✏️ أرسل الآن طلبك الخاص بـ {current_service}، مثال: (اسم المنتج أو الطلب)"
        else:
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."

    # حفظ الطلب فقط إذا الحالة انتظار إدخال طلب للخدمة الصحيحة
    if current_state and current_state.startswith("waiting_input_"):
        # منع أرقام الخدمات كطلب أثناء انتظار إدخال الطلب
        if msg in allowed_service_ids:
            new_service_name = allowed_service_ids[msg]
            user_states[user_id] = f"awaiting_order_{new_service_name}"
            response = f"*📦 {new_service_name}:*\n"
            for i, store in enumerate(stores_list, 1):
                response += f"{i}. {store}\n"
            response += "\n99. اطلب الآن"
            return response
        # منع الطلبات الفارغة
        if not msg or len(msg) < 2:
            return "❗️الطلب المدخل غير صحيح. الرجاء كتابة الطلب بشكل واضح."
        current_service = current_state.replace("waiting_input_", "")
        save_order(user_id, current_service, msg)
        user_states[user_id] = f"awaiting_order_{current_service}"
        return f"✅ تم حفظ طلبك: {msg}\n\nأرسل 99 لإضافة طلب آخر، أو 0 للرجوع للقائمة، أو 20 لمشاهدة طلباتك."

    # عرض الطلبات عند اختيار 20
    if msg == "20":
        return get_orders_for_user(user_id)

    return None
