import time

ORDER_PREFIX = "G"

def send_message(chat_id, text):
    """
    ترسل رسالة للمستخدم عبر البوت.
    يمكنك تعديل الكود حسب طريقة الإرسال الخاصة بك.
    """
    # مثال:
    # bot.send_message(chat_id, text)
    pass

def generate_order_id():
    """
    توليد رقم طلب مكوّن من حرف و3 أرقام فقط (مثل: G001)
    يبدأ العد من جديد كل يوم.
    """
    # نحصل على تاريخ اليوم بصيغة يوم-شهر-سنة
    day = time.strftime("%d%m%y")
    counter_file = f"order_counter_{day}.txt"
    try:
        with open(counter_file, "r") as f:
            last_number = int(f.read().strip())
    except:
        last_number = 0
    new_number = (last_number + 1) % 1000  # من 1 إلى 999 فقط
    with open(counter_file, "w") as f:
        f.write(str(new_number))
    return f"{ORDER_PREFIX}{new_number:03d}"

# مثال على الاستخدام
if __name__ == "__main__":
    order_id = generate_order_id()
    print(f"رقم الطلب الجديد: {order_id}")