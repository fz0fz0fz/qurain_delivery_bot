from init_db import init_db
init_db()

# ✅ كود طباعة الجداول (احذفه بعد التأكد)
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

# باقي الاستيرادات
from flask import Flask, request
from dispatcher import dispatch_message

app = Flask(__name__)

# تخزين حالات المستخدمين والطلبات مؤقتًا في الذاكرة
user_states = {}
user_orders = {}

@app.route("/", methods=["GET"])
def index():
    return "🚀 Qurain Delivery Bot is Live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "❌ No data received", 400

    payload = data.get("data", {})
    user_id = payload.get("from")
    message = payload.get("body")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")

    if not user_id or not message:
        return "❌ Missing fields", 400

    # إذا كانت رسالة من المندوب (يحتوي على كلمة "قبول")
    driver_id = None
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

    return "✅ OK", 200
