import os
import requests

def send_message(phone, message):
    """
    يرسل رسالة واتساب باستخدام Wasender API ويطبع نتيجة الرد دائماً في اللوق.
    """
    api_key = os.getenv("WASENDER_API_KEY")
    if not api_key:
        print("❌ تأكد من ضبط متغير البيئة WASENDER_API_KEY")
        raise EnvironmentError("WASENDER_API_KEY must be set in environment variables.")

    url = "https://api.wasender.io/api/v1/sendMessage"  # قد يختلف حسب توثيق Wasender
    payload = {
        "api_key": api_key,
        "to": phone,      # بصيغة دولية مثل: 9665XXXXXXXX
        "message": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("Wasender Response:", response.text)  # طباعة الرد دائماً مهما كان
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"error": str(e)}