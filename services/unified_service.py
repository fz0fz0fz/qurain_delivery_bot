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

    # إذا دخل المستخدم على خدمة من القائمة (مثل: 2 أو 3 أو 1)
    if msg == service_id:
        user_states[user_id] = f"awaiting_order_{service_name}"
        response = f"*📦 {service_name}:*\n"
        for i, store in enumerate(stores_list, 1):
            response += f"{i}. {store}\n"
        response += "\n99. اطلب الآن"
        return response

    # إذا أرسل المستخدم "99"، يجب استخراج اسم الخدمة من الحالة وليس من متغير ثابت
    if msg == "99":
        current_state = user_states.get(user_id)
        if current_state and current_state.startswith("awaiting_order_"):
            # استخرج اسم الخدمة المختارة حاليا
            current_service = current_state.replace("awaiting_order_", "")
            user_states[user_id] = f"waiting_input_{current_service}"
            return f"✏️ أرسل الآن طلبك الخاص بـ {current_service}، مثال: (اسم المنتج أو الطلب)"
        else:
            return "❗️يجب اختيار خدمة من القائمة أولًا ثم الضغط 99 لإضافة طلب."

    # إذا أرسل المستخدم الطلب الفعلي
    current_state = user_states.get(user_id)
    if current_state and current_state.startswith("waiting_input_"):
        current_service = current_state.replace("waiting_input_", "")
        save_order(user_id, current_service, msg)
        user_states[user_id] = f"awaiting_order_{current_service}"
        return f"✅ تم حفظ طلبك: {msg}\n\nأرسل 99 لإضافة طلب آخر، أو 0 للرجوع للقائمة، أو 20 لمشاهدة طلباتك."

    # أي حالة أخرى → يتم تجاهلها
    return None