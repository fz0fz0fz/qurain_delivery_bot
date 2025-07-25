# mandoubs.py

mandoubs = [
    {"id": "966503813344", "name": "مندوب 1", "available": True},
    {"id": "966507005272", "name": "مندوب 2", "available": True}
]

def get_next_mandoub(excluded_ids):
    """
    ترجع أول مندوب متاح لم يُرسل له الطلب سابقًا.
    """
    for mandoub in mandoubs:
        if mandoub["available"] and mandoub["id"] not in excluded_ids:
            return mandoub["id"]
    return None  # لا يوجد مناديب متاحين
