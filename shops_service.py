# -*- coding: utf-8 -*-
"""
منطق خدمة (7) المحلات (بدون تصنيفات).
التحديث الحالي:
- إضافة وصف للمحل (اختياري) متعدد الأسطر.
سير التسجيل:
  الاسم -> رقم الجوال -> الوصف (اختياري متعدد الأسطر ينتهي بـ (تم) أو (لا يوجد)) -> الموقع (إلزامي) -> الروابط (اختياري) -> تأكيد.
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime

DATA_FILE = "data/shops_data.json"
ADMIN_PHONE = "0503813344"  # رقم المشرف

DEFAULT_DATA = {
    "shops": [],
    "last_shop_id": 0
}

memory_sessions: Dict[str, Dict[str, Any]] = {}

# الحقول الإلزامية (الوصف ليس إلزامياً)
REQUIRED_FIELDS = ["name", "phone", "maps"]
REQUIRE_AT_LEAST_ONE_LINK = False  # الروابط اختيارية

def load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return DEFAULT_DATA.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DATA.copy()

def save_data(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_session(user_id: str) -> Dict[str, Any]:
    return memory_sessions.setdefault(user_id, {"state": "idle"})

def reset_session(user_id: str):
    memory_sessions[user_id] = {"state": "idle"}

# ---------- الأدوات المساعدة ----------

def is_google_maps_link(text: str) -> bool:
    t = text.lower()
    return ("maps" in t or "goo.gl" in t) and (t.startswith("http://") or t.startswith("https://"))

def is_coordinates(text: str) -> bool:
    t = text.strip().replace("ـ", "")
    if "," in t:
        parts = [p.strip() for p in t.split(",")]
        if len(parts) == 2:
            try:
                float(parts[0]); float(parts[1])
                return True
            except ValueError:
                return False
    return False

def format_shop(shop: Dict[str, Any], index: int = None) -> List[str]:
    lines = []
    prefix = f"{index}. " if index is not None else ""
    lines.append(f"{prefix}🏪 {shop['name']}")
    lines.append(f"📞 {shop['phone']}")
    lines.append(f"📍 {shop['maps']}")
    desc = shop.get("desc")
    if desc:
        lines.append(f"📝 {desc}")
    if shop.get("links"):
        if len(shop["links"]) == 0:
            lines.append("🔗 لا توجد روابط")
        else:
            for ln in shop["links"]:
                lines.append(f"🔗 {ln}")
    else:
        lines.append("🔗 لا توجد روابط")
    return lines

def list_shops(data: Dict[str, Any]) -> str:
    shops = data.get("shops", [])
    if not shops:
        return (
            "🏪 *دليل المحلات (لا توجد محلات مسجلة حالياً)*\n"
            "أرسل 77 لتسجيل محل جديد.\n"
            "للمشرف: حذف <رقم_المحل>\n"
            "🔄 أرسل 0 للعودة."
        )
    lines = ["🏪 *دليل المحلات*",""]
    for idx, s in enumerate(shops, start=1):
        lines.extend(format_shop(s, idx))
        lines.append("")
    lines.append("أرسل 77 لتسجيل محل جديد. للمشرف: حذف 3 مثلاً لحذف المحل رقم 3.")
    lines.append("🔄 أرسل 0 للعودة.")
    return "\n".join(lines)

# ---------- التسجيل ----------

def start_registration(user_id: str) -> str:
    s = get_session(user_id)
    s["state"] = "reg_name"
    s["new_shop"] = {}
    s.pop("temp_links", None)
    s.pop("temp_desc_lines", None)
    return ("📝 *تسجيل محل جديد*\n"
            "أدخل اسم المحل:")

def handle_registration(user_id: str, text: str, data: Dict[str, Any]) -> str:
    s = get_session(user_id)
    ns = s.get("new_shop", {})
    t = text.strip()

    if s["state"] == "reg_name":
        if not t:
            return "⚠️ الاسم مطلوب، أدخل اسم المحل:"
        ns["name"] = t
        s["state"] = "reg_phone"
        return "أدخل رقم الجوال (لن يُقبل رقم مكرر):"

    elif s["state"] == "reg_phone":
        if not t:
            return "⚠️ رقم الجوال مطلوب. أعد الإدخال:"
        if any(shop["phone"] == t for shop in data["shops"]):
            return "⚠️ هذا الرقم مسجّل مسبقاً. أدخل رقم آخر:"
        ns["phone"] = t
        s["state"] = "reg_desc"
        return (
            "أدخل وصفاً مختصراً للمحل (اختياري، يمكن أن يكون عدة أسطر).\n"
            "مثال: محل متخصص في بيع الأدوات المنزلية والهدايا.\n"
            "اكتب الأسطر ثم أرسل (تم) عند الانتهاء أو (لا يوجد) لتخطي."
        )

    elif s["state"] == "reg_desc":
        # تجميع متعدد الأسطر
        if t == "":
            return "أضف سطر أو أرسل (تم) أو (لا يوجد):"
        if t in ["لا يوجد","لايوجد"]:
            ns["desc"] = ""
            s.pop("temp_desc_lines", None)
            s["state"] = "reg_maps"
            return (
                "أدخل موقع المحل (إلزامي):\n"
                "- إذا أنت داخل المحل: أرسل (مشاركة الموقع).\n"
                "- إذا بعيد: الصق رابط خرائط Google (مثال: https://maps.app.goo.gl/...)\n"
                "أدخل الآن:"
            )
        if t == "تم":
            # إنهاء التجميع
            desc_lines = s.get("temp_desc_lines", [])
            ns["desc"] = "\n".join(desc_lines).strip()
            s.pop("temp_desc_lines", None)
            s["state"] = "reg_maps"
            return (
                "أدخل موقع المحل (إلزامي):\n"
                "- إذا أنت داخل المحل: أرسل (مشاركة الموقع).\n"
                "- إذا بعيد: الصق رابط خرائط Google (مثال: https://maps.app.goo.gl/...)\n"
                "أدخل الآن:"
            )
        # إضافة سطر
        lines_acc = s.setdefault("temp_desc_lines", [])
        lines_acc.append(t)
        return "سطر محفوظ. أضف سطر آخر أو أرسل (تم) للمتابعة أو (لا يوجد) لتخطي."

    elif s["state"] == "reg_maps":
        if not t:
            return "⚠️ الموقع مطلوب. أدخل رابط خرائط أو أرسل الموقع:"
        if is_google_maps_link(t) or is_coordinates(t):
            ns["maps"] = t
            s["state"] = "reg_links"
            return (
                "أدخل روابط الحسابات (سناب/إنستقرام/أي) كل رابط في سطر (اختياري).\n"
                "اكتب (لا يوجد) إذا لا توجد روابط.\n"
                "أرسل (حفظ) للانتقال إلى المراجعة متى انتهيت."
            )
        else:
            return "⚠️ صيغة غير مقبولة. أدخل رابط خرائط صحيح أو إحداثيات (مثال: 24.12345, 45.67890):"

    elif s["state"] == "reg_links":
        links_arr = s.setdefault("temp_links", [])
        if t == "حفظ":
            if links_arr == ["__NONE__"]:
                links_arr = []
            ns["links"] = links_arr
            s["state"] = "reg_confirm"
            return build_confirmation(ns)
        if t == "لا يوجد":
            s["temp_links"] = ["__NONE__"]
            return "تم تسجيل عدم وجود روابط. أرسل (حفظ) للمراجعة أو أضف روابط بدلاً عنها."
        links_arr.append(t)
        return "✅ تم إضافة الرابط. أضف رابط آخر أو أرسل (حفظ)."

    elif s["state"] == "reg_confirm":
        low = t.lower()
        if low in ["حفظ","save"]:
            missing = [f for f in REQUIRED_FIELDS if not ns.get(f)]
            if missing:
                s["state"] = "reg_name"
                return f"⚠️ حقول ناقصة: {missing}. نعيدك للبداية."
            finalize_registration(user_id, data, ns)
            reset_session(user_id)
            return "✅ تم تسجيل المحل بنجاح. أرسل 7 لعرض القائمة."
        elif low in ["الغاء","إلغاء","cancel"]:
            reset_session(user_id)
            return "تم إلغاء التسجيل. أرسل 7 للعودة."
        else:
            return "اكتب (حفظ) لتأكيد التسجيل أو (إلغاء) للتراجع."

    else:
        return "⚠️ حالة غير متوقعة. أرسل 7 للبدء من جديد."

def build_confirmation(ns: Dict[str, Any]) -> str:
    links_render = ns.get("links", [])
    if not links_render:
        links_text = "🔗 لا توجد روابط"
    else:
        links_text = "\n".join(f"🔗 {l}" for l in links_render)
    desc_part = f"📝 الوصف:\n{ns['desc']}\n" if ns.get("desc") else "📝 الوصف: لا يوجد\n"
    lines = [
        "📋 *مراجعة البيانات:*",
        f"🏪 الاسم: {ns.get('name')}",
        f"📞 الجوال: {ns.get('phone')}",
        f"📍 الموقع: {ns.get('maps')}",
        desc_part.rstrip(),
        links_text,
        "",
        "أرسل (حفظ) للتخزين أو (إلغاء) للتراجع."
    ]
    return "\n".join(lines)

def finalize_registration(user_id: str, data: Dict[str, Any], ns: Dict[str, Any]):
    data["last_shop_id"] = data.get("last_shop_id", 0) + 1
    ns["id"] = data["last_shop_id"]
    ns["status"] = "approved"
    ns["created_by"] = user_id
    ns["created_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    data["shops"].append(ns)
    save_data(data)

# ---------- حذف (للمشرف) ----------

def attempt_delete(user_id: str, text: str, data: Dict[str, Any]) -> str:
    parts = text.strip().split()
    if len(parts) != 2:
        return "صيغة الحذف غير صحيحة. استخدم: حذف <رقم_المحل>"
    _, idx_str = parts
    if not idx_str.isdigit():
        return "⚠️ رقم المحل يجب أن يكون رقماً."
    if user_id != ADMIN_PHONE:
        return "⛔ ليس لديك صلاحية الحذف."
    idx = int(idx_str)
    shops = data.get("shops", [])
    if idx < 1 or idx > len(shops):
        return "⚠️ رقم محل غير موجود."
    shop = shops[idx - 1]
    del shops[idx - 1]
    save_data(data)
    return f"✅ تم حذف: {shop.get('name','')} (رقم {idx}). أرسل 7 لتحديث القائمة."

# ---------- استقبال رسالة موقع فعلية (اختياري) ----------
def handle_location_message(user_id: str, latitude: float, longitude: float) -> str:
    data = load_data()
    s = get_session(user_id)
    if s.get("state") != "reg_maps":
        return "تم استلام الموقع، لكنك لست في خطوة إدخال الموقع. أرسل 7 للبدء."
    ns = s.get("new_shop", {})
    ns["maps"] = f"{latitude:.6f}, {longitude:.6f}"
    s["state"] = "reg_links"
    return (
        "✅ تم استلام الموقع بالإحداثيات.\n"
        "أدخل الآن الروابط (اختياري) كل رابط بسطر، أو اكتب (لا يوجد)، ثم (حفظ)."
    )

# ---------- نقطة الدخول الرئيسية ----------

def handle_shops(user_id: str, text: str) -> str:
    data = load_data()
    s = get_session(user_id)
    t = text.strip()

    if t == "7" and s["state"] == "idle":
        return list_shops(data)
    if t == "77" and s["state"] == "idle":
        return start_registration(user_id)
    if t.startswith("حذف ") or t.lower().startswith(("delete ","del ")):
        return attempt_delete(user_id, t, data)
    if s["state"].startswith("reg_"):
        return handle_registration(user_id, t, data)
    if s["state"] == "idle":
        if t == "7":
            return list_shops(data)
        return "أرسل 7 لعرض المحلات أو 77 لتسجيل محل جديد."
    return "أرسل 7 لعرض المحلات."
