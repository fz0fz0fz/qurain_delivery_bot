import os
import requests

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
