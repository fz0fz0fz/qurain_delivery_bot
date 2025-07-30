from init_db import init_db
init_db()

import sqlite3
DB_PATH = "orders.db"
def print_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    conn.close()
    print("📦 الجداول الموجودة:", [t[0] for t in tables])
print_tables()

from flask import Flask, request
from dispatcher import dispatch_message
from send_utils import send_message  # تأكد من الاستيراد هنا

app = Flask(__name__)

user_states = {}
user_orders = {}

@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("بيانات الواتساب الواردة:", data)

    if not data:
        return "❌ No data received", 400

    payload = data.get("data", {})

    user_id = payload.get("from")
    message = payload.get("body")
    driver_id = None
    latitude = None
    longitude = None

    # إذا كانت الرسالة من نوع "location" استخرج الإحداثيات من مفتاح location
    if payload.get("type") == "location":
        location = payload.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")
    else:
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

    if not user_id or not message:
        return "❌ Missing fields", 400

    if "قبول" in message:
        driver_id = user_id

    response = dispatch_message(
        user_id=user_id,
        message=message,
        user_states=user_states,
        user_orders=user_orders,
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude
    )

    if response:
        phone = user_id.split("@")[0] if "@c.us" in user_id else user_id
        send_message(phone, response)

    return "✅ OK", 200
import menu_app