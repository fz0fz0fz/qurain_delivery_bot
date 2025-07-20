
from flask import Flask, request
from dispatcher import process_order

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    sender = data.get('from')
    message = data.get('body')

    if message.startswith("أحتاج") or message.startswith("طلب"):
        process_order(sender, message)
        return "تم استقبال الطلب", 200
    return "جاهز", 200

if __name__ == '__main__':
    app.run(debug=True)
