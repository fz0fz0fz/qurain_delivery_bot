def send_order(number, order_id, items):
    msg = f"📦 طلب رقم {order_id} من عميل.\nيرجى تجهيز:\n- " + "\n- ".join(items)
    print(f"📲 [خضار] إلى {number}: {msg}")
