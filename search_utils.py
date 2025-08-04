# search_utils.py

import re

def normalize_arabic(text):
    """توحيد الحروف العربية المشابهة لتسهيل البحث."""
    text = str(text)
    text = re.sub("[أإآا]", "ا", text)
    text = re.sub("[ةه]", "ه", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ؤ", "و", text)
    text = re.sub("ئ", "ي", text)
    text = re.sub("ـ", "", text)  # حذف الكشيدة
    text = re.sub("[ًٌٍَُِّْ]", "", text)  # حذف التشكيل
    return text

def search_services_arabic(keyword, services_dict):
    """بحث متقدم يتجاهل الفرق بين الحروف العربية ويبحث في كل الخدمات."""
    results = []
    keyword_norm = normalize_arabic(keyword).replace(" ", "")
    for service in services_dict.values():
        # بحث في العناصر العادية
        for item in service.get("items", []):
            name_norm = normalize_arabic(item["name"]).replace(" ", "")
            if keyword_norm in name_norm:
                results.append({"name": item["name"], "phone": item["phone"]})
        # بحث في عناصر الطوارئ لو موجودة
        for em in service.get("emergency", []):
            name_norm = normalize_arabic(em["name"]).replace(" ", "")
            if keyword_norm in name_norm:
                results.append({"name": em["name"], "phone": ""})
        # بحث في الخدمات المتشعبة (لو موجودة)
        for sub in service.get("sub_services", {}).values():
            for item in sub.get("items", []):
                name_norm = normalize_arabic(item["name"]).replace(" ", "")
                if keyword_norm in name_norm:
                    results.append({"name": item["name"], "phone": item["phone"]})
    return results