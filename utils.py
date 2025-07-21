import random
import string
import requests
import os

def generate_order_id():
    return "G" + ''.join(random.choices(string.digits, k=3))

def send_message(phone, message):
    instance_id = os.getenv("ULTRA_INSTANCE_ID")
    token = os.getenv("ULTRA_TOKEN")
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"

    payload = {
        "to": phone,
        "body": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, params={"token": token})
    return response.json()
