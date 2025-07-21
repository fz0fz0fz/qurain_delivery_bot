import requests

ULTRAMSG_URL = "https://api.ultramsg.com/instance130542/messages/chat"
ULTRAMSG_TOKEN = "9dxefhg0k4l3b7ak"

def send_whatsapp(to, message):
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    requests.post(ULTRAMSG_URL, data=payload)

def handle_pharmacy(sender, message):
    if message == "2":
        reply = """*[2] قائمة الصيدليات:*

1- صيدلية ركن أطلس (القرين)
__________________________
2- صيدلية دواء البدر (الدليمية)
__________________________
3- صيدلية ساير (الدليمية)

*99 - إطلب*: ستجد طلباتك كاملة في رقم 20 من القائمة الرئيسية."""
        send_whatsapp(sender, reply)

    elif message == "99":
        send_whatsapp(sender, "📦 أرسل طلبك الآن بصيغة واضحة، وسنقوم بعرضه في قائمة 'طلباتك'.")
    
    else:
        send_whatsapp(sender, "❓ يرجى اختيار رقم من القائمة أو إرسال 99 للطلب.")
