import os
import time
import requests

ORDER_PREFIX = "G"  # يمكنك تغيير البادئة إذا أحببت

def generate_order_id():
    """
    ينشئ رقم طلب فريد كل يوم يبدأ بالحرف G ويزداد مع كل طلب جديد.
    """
    day = time.strftime("%d%m%y")
    counter_file = f"order_counter_{day}.txt"
    try:
        with open(counter_file, "r") as f:
            last_number = int(f.read().strip())
    except:
        last_number = 0
    new_number = (last_number + 1) % 1000
    with open(counter_file, "w") as f:
        f.write(str(new_number))
    return f"{ORDER_PREFIX}{new_number:03d}"

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