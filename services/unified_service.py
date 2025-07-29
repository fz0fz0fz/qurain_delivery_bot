import sqlite3
from datetime import datetime

def save_order(user_id, service_name, order_text):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute(
        'INSERT INTO orders (user_id, service_name, order_text, created_at) VALUES (?, ?, ?, ?)',
        (user_id, service_name, order_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def handle_service(user_id, message, user_states, user_orders, service_id, service_name, stores_list):
    msg = message.strip()

    # المستخدم دخل على خدمة معينة (مثل: 2 أو 3)
    if msg == service_id:
        user_states[user_id] = f"awaiting_order_{service_name}"
        response = f"*📦 {service_name}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # المستخدم كتب "99" ولكن هل هو داخل الخدمة؟
    if msg == "99":
        if user_states.get(user_id) == f"awaiting_order_{service_name}":
            user_states[user_id] = f"waiting_input_{service_name}"
            return f"✏️ أرسل الآن طلبك الخاص بـ {service_name}، مثال: (اسم المنتج أو الطلب)"
        else:
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."

    # المستخدم أرسل الطلب الفعلي (مثلاً: بنادول)
    if user_states.get(user_id) == f"waiting_input_{service_name}":
        save_order(user_id, service_name, msg)
        user_states[user_id] = f"awaiting_order_{service_name}"
        return f"✅ تم حفظ طلبك: {msg}\n\nأرسل 99 لإضافة طلب آخر، أو 0 للرجوع للقائمة، أو 20 لمشاهدة طلباتك."

    # أي حالة أخرى → يتم تجاهلها
    return None