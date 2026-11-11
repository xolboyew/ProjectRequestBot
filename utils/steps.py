"""Ariza savollari (ketma-ket beriladi)."""
STEPS: list[dict] = [
    {"field": "bot_type", "label": "Bot turi", "kind": "text", "required": True,
     "q": "Qanday Telegram bot kerak?",
     "hint": "Masalan: onlayn do'kon boti, buyurtma qabul qilish boti, CRM, o'quv markaz boti…"},
    {"field": "bot_name", "label": "Bot nomi", "kind": "text", "required": False,
     "q": "Botning nomi qanday bo'lsin?",
     "hint": "Masalan: <i>Oila Market</i>"},
    {"field": "bot_username", "label": "Bot username", "kind": "username", "required": False,
     "q": "Bot username'i qanday bo'lsin?",
     "hint": "Masalan: <code>@MyProjectBot</code> (username <code>bot</code> so'zi bilan tugashi shart)"},
    {"field": "purpose", "label": "Bot vazifasi", "kind": "text", "required": True,
     "q": "Bot nima vazifani bajarishi kerak?",
     "hint": "Asosiy maqsadni 1–2 gapda yozing."},
    {"field": "features", "label": "Kerakli funksiyalar", "kind": "text", "required": True,
     "q": "Bot qanday imkoniyatlarga ega bo'lishi kerak?",
     "hint": "Masalan: katalog, savat, to'lov, bildirishnoma, til tanlash…"},
    {"field": "admin_panel", "label": "Admin panel", "kind": "choice", "required": False,
     "q": "Botda admin panel kerakmi?",
     "hint": "Tugmalardan birini tanlang yoki o'zingiz yozing."},
    {"field": "extra_requirements", "label": "Qo'shimcha talablar", "kind": "text", "required": False,
     "q": "Qo'shimcha talablaringiz bormi?",
     "hint": "Dizayn, til, muddat, byudjet kabi istaklaringiz."},
    {"field": "extra_info", "label": "Qo'shimcha ma'lumot / havola", "kind": "multi", "required": False,
     "q": "Loyihaga oid qo'shimcha ma'lumot yoki havola yuborishingiz mumkin.",
     "hint": "Matn, rasm, video yoki hujjat yuboring. Bir nechta xabar yuborish mumkin — "
             "tugagach <b>Tayyor</b> tugmasini bosing."},
]
TOTAL_STEPS = len(STEPS)
MAX_TEXT = 1500
MAX_FILES = 10
