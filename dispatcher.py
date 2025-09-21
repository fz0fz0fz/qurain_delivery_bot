from driver_register import handle_driver_service, delete_driver
from send_utils import send_message
from services_data import SERVICES

allowed_service_ids = {
    "11": "عمال",
    "14": "نقل مدرسي ومشاوير",
    "15": "تأجير"
}

main_menu_text = (
    "📖 *دليلك لخدمات القرين*\n"
    "👋 أهلاً وسهلاً بك! اختر رقم الخدمة من القائمة أدناه، أو أرسل `0` للعودة للقائمة الرئيسية في أي وقت.\n\n"
    "*📋 الخدمات المتاحة:*\n\n"
    "11. عمال 👷\n"
    "14. نقل مدرسي ومشاوير 🚍\n"
    "15. تأجير 📦\n"
    "━━━━━━━━━━━━━━━\n"
    "✉️ للاقتراحات: أرسل `100`\n"
    "━━━━━━━━━━━━━━━"
)

def handle_main_menu(message):
    if message.strip() in ["0", ".", "٠", "خدمات"]:
        return main_menu_text
    return None

def handle_feedback(user_id, message, user_states):
    if message.strip() == "100":
        user_states[user_id] = "awaiting_feedback"
        return "✉️ أرسل الآن رسالتك (اقتراح أو شكوى)"
    elif user_states.get(user_id) == "awaiting_feedback":
        user_states.pop(user_id, None)
        send_message("966503813344", f"💬 شكوى من {user_id}:\n{message}")
        return "✅ تم استلام رسالتك، شكرًا لك."
    return None

def dispatch_message(user_id, message, user_states):
    msg = message.strip()

    # القائمة الرئيسية
    response = handle_main_menu(msg)
    if response: return response

    # استقبال اقتراحات/شكاوى
    response = handle_feedback(user_id, msg, user_states)
    if response: return response

    # منطق خدمة السائقين (نقل مدرسي ومشاوير)
    if (
        msg == "14"
        or user_states.get(user_id) == "awaiting_driver_register"
        or msg == "88"
        or msg.startswith("سائق")
        or user_states.get(user_id) in [
            "awaiting_driver_name",
            "awaiting_driver_phone",
            "awaiting_driver_description",
            "awaiting_driver_delete_number"
        ]
    ):
        response = handle_driver_service(user_id, msg, user_states)
        if response:
            return response

    # الخدمات الأخرى من SERVICES (عمال، تأجير)
    if msg in allowed_service_ids:
        service_id = msg
        service_data = SERVICES[service_id]
        if "display_msg" in service_data:
            return service_data["display_msg"]
        else:
            # إذا كانت توجد عناصر فقط (مثلاً قائمة عمال أو تأجير)
            items = service_data.get("items", [])
            if items:
                res = f"*{service_data.get('name', '')}:*\n"
                for i, item in enumerate(items, 1):
                    res += f"{i}. {item['name']} - {item.get('phone','')}\n"
                res += "\n🔄 أرسل 0 للعودة للقائمة الرئيسية"
                return res
            else:
                return f"لا توجد بيانات حالياً لخدمة {service_data.get('name','')}.\n🔄 أرسل 0 للعودة للقائمة الرئيسية"

    return "❗️يرجى اختيار رقم خدمة من القائمة أولًا."