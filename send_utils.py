import sqlite3
import os
import requests

ORDER_PREFIX = "G"  # يمكنك تغيير البادئة إذا أحببت
DB_PATH = "orders.db"

def generate_order_id():
    """
    ينشئ رقم طلب متسلسل يبدأ بالحرف G ويستمر مع كل طلب جديد حتى بعد إعادة تشغيل السيرفر.
    يعتمد على آخر رقم طلب مخزن في قاعدة البيانات.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT order_number FROM orders WHERE order_number IS NOT NULL ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        last_number = row[0]
        # يستخرج الرقم الرقمي من آخر رقم طلب
        prefix = ''.join([ch for ch in last_number if not ch.isdigit()]) or ORDER_PREFIX
        number = ''.join([ch for ch in last_number if ch.isdigit()])
        number = int(number) if number else 0
        new_number = number + 1
        return f"{prefix}{new_number:03d}"
    else:
        return f"{ORDER_PREFIX}001"

def send_message(phone, message):
    """
    يرسل رسالة واتساب باستخدام UltraMsg API ويطبع نتيجة الرد دائماً في اللوق.
    """
    instance_id = os.getenv("ULTRA_INSTANCE_ID")
    token = os.getenv("ULTRA_TOKEN")
    if not instance_id or not token:
        print("❌ تأكد من ضبط متغيرات البيئة ULTRA_INSTANCE_ID و ULTRA_TOKEN")
        raise EnvironmentError("ULTRA_INSTANCE_ID and ULTRA_TOKEN must be set in environment variables.")

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "to": phone,    # يجب أن يكون بصيغة دولية مثل: 9665XXXXXXXX
        "body": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, params={"token": token}, timeout=10)
        print("UltraMsg Response:", response.text)  # طباعة الرد دائماً مهما كان
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"error": str(e)}