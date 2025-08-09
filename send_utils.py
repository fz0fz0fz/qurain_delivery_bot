# send_utils.py
import os, json, requests

SESSION = requests.Session()
BASE = "https://wasenderapi.com/api"
SEND_ENDPOINT = f"{BASE}/send-message"
API_KEY = os.getenv("WASENDER_API_KEY")

def send_message(to, text=None, image_url=None, document_url=None, location=None, timeout=10):
    if not API_KEY:
        raise EnvironmentError("WASENDER_API_KEY not set")

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"to": to}
    if text: payload["text"] = text
    if image_url: payload["image"] = {"url": image_url}
    if document_url: payload["document"] = {"url": document_url}
    if location:
        payload["location"] = {
            "latitude": float(location["latitude"]),
            "longitude": float(location["longitude"]),
            **({"name": location.get("name")} if location.get("name") else {})
        }

    r = SESSION.post(SEND_ENDPOINT, headers=headers, json=payload, timeout=timeout)
    print("WaSender Request:", json.dumps(payload, ensure_ascii=False))
    print("WaSender Response Status:", r.status_code)
    print("WaSender Response Body:", r.text)
    r.raise_for_status()
    return r.json() if r.headers.get("content-type","").startswith("application/json") else {"raw": r.text}