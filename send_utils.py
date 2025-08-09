import os
import json
import requests

WASENDER_BASE_URL = "https://wasenderapi.com/api"
SEND_ENDPOINT = f"{WASENDER_BASE_URL}/send-message"

def send_message(to, text=None, image_url=None, document_url=None, location=None, timeout=15):
    """
    إرسال رسالة عبر WaSenderAPI.
    - to: رقم بصيغة دولية +9665XXXXXXX (مُفضل) أو JID.
    - text: نص الرسالة (اختياري إذا أرسلت ميديا/موقع).
    - image_url: رابط صورة مباشر (اختياري).
    - document_url: رابط ملف مباشر (اختياري).
    - location: dict مثل {"latitude": 24.774265, "longitude": 46.738586, "name": "Riyadh"} (اختياري).
    - timeout: مهلة الطلب بالثواني.
    """
    api_key = os.getenv("WASENDER_API_KEY")
    if not api_key:
        msg = "❌ تأكد من ضبط متغير البيئة WASENDER_API_KEY"
        print(msg)
        raise EnvironmentError(msg)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {"to": to}

    if text:
        payload["text"] = text
    if image_url:
        payload["image"] = {"url": image_url}
    if document_url:
        payload["document"] = {"url": document_url}
    if location:
        # توقع الحقول: latitude, longitude, name (اختياري)
        payload["location"] = {
            "latitude": float(location.get("latitude")),
            "longitude": float(location.get("longitude")),
            **({"name": location.get("name")} if location.get("name") else {})
        }

    # تحذير مبكر لو ما في أي محتوى
    if not any([text, image_url, document_url, location]):
        raise ValueError("يجب تمرير واحد على الأقل من: text, image_url, document_url, location")

    try:
        resp = requests.post(SEND_ENDPOINT, headers=headers, json=payload, timeout=timeout)
        # اطبع دائمًا للوغ
        print("WaSender Request:", json.dumps(payload, ensure_ascii=False))
        print("WaSender Response Status:", resp.status_code)
        print("WaSender Response Body:", resp.text)
        resp.raise_for_status()

        # حاول إرجاع JSON وإلا أرجع النص
        try:
            return resp.json()
        except ValueError:
            return {"ok": True, "raw": resp.text}

    except requests.exceptions.RequestException as e:
        # طباعة الخطأ وإرجاعه كقاموس
        print(f"Error sending message: {e}")
        return {"error": str(e)}