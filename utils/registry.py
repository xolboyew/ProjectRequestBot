"""
Barcha sozlanadigan tugma va emoji "slot"lari.

Har bir slot: kalit, guruh, standart matn, standart (oddiy) emoji, standart rang.
Admin paneldan har bir slot uchun matn, rang (style) va premium emoji ID o'zgartiriladi.
Premium emoji ID'lari kodda YO'Q — admin ularni panel orqali haqiqiy premium emoji yuborib belgilaydi.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Slot:
    key: str
    group: str
    label: str
    emoji: str
    style: str | None = None  # primary (ko'k) | success (yashil) | danger (qizil) | None


GROUPS: dict[str, str] = {
    "menu": "📱 Asosiy menyu",
    "flow": "📝 Ariza berish tugmalari",
    "reg": "🪪 Ro'yxatdan o'tish",
    "profile": "👤 Profil tugmalari",
    "client": "💬 Mijoz tugmalari",
    "nav": "🧭 Umumiy tugmalar",
    "adminp": "👑 Admin panel",
    "adminact": "🛠 Ariza boshqaruvi",
    "settings": "⚙️ Sozlamalar tugmalari",
    "sub": "🔒 Majburiy obuna",
    "status": "🚦 Ariza holatlari",
    "emoji": "✨ Matndagi emojilar",
}

_S = Slot
SLOT_LIST: list[Slot] = [
    # --- Asosiy menyu
    _S("m_create", "menu", "Bot yaratish", "🤖", "success"),
    _S("m_orders", "menu", "Arizalarim", "📂", "primary"),
    _S("m_status", "menu", "Ariza holati", "📊", "primary"),
    _S("m_profile", "menu", "Mening profilim", "👤", "primary"),
    _S("m_contact", "menu", "Aloqa", "📞", "success"),
    _S("m_about", "menu", "Bot haqida", "ℹ️", "primary"),
    _S("m_admin", "menu", "Boshqaruv", "🎛", "danger"),
    # --- Ariza berish
    _S("f_back", "flow", "Orqaga", "⬅️", "primary"),
    _S("f_cancel", "flow", "Bekor qilish", "❌", "danger"),
    _S("f_skip", "flow", "O'tkazib yuborish", "⏭", "primary"),
    _S("f_done", "flow", "Tayyor", "✅", "success"),
    _S("f_yes", "flow", "Ha, kerak", "✅", "success"),
    _S("f_no", "flow", "Yo'q, kerak emas", "🚫", "danger"),
    _S("f_confirm", "flow", "Arizani tasdiqlash", "✅", "success"),
    _S("f_edit", "flow", "Tahrirlash", "✏️", "primary"),
    _S("f_new", "flow", "Yangi ariza", "➕", "success"),
    _S("f_field", "flow", "Maydon", "🔹", "primary"),
    # --- Ro'yxatdan o'tish
    _S("r_phone", "reg", "Telefon raqamni yuborish", "📱", "success"),
    _S("r_location", "reg", "Joylashuvni yuborish", "📍", "success"),
    # --- Profil
    _S("p_name", "profile", "Ism-familiyani o'zgartirish", "✏️", "primary"),
    _S("p_phone", "profile", "Telefonni yangilash", "📱", "primary"),
    _S("p_loc", "profile", "Joylashuvni yangilash", "📍", "primary"),
    # --- Mijoz
    _S("o_contact", "client", "Admin bilan bog'lanish", "💬", "success"),
    _S("o_reply", "client", "Javob yozish", "↩️", "success"),
    _S("c_write", "client", "Adminga yozish", "✉️", "success"),
    _S("c_general", "client", "Umumiy savol", "❓", "primary"),
    _S("c_tg", "client", "Telegramda yozish", "✈️", "primary"),
    # --- Umumiy
    _S("n_prev", "nav", "Oldingi", "◀️", "primary"),
    _S("n_next", "nav", "Keyingi", "▶️", "primary"),
    _S("n_back", "nav", "Orqaga", "⬅️", "primary"),
    _S("n_home", "nav", "Bosh sahifa", "🏠", "primary"),
    _S("n_close", "nav", "Yopish", "✖️", "danger"),
    # --- Admin panel
    _S("a_new", "adminp", "Yangi arizalar", "📥", "primary"),
    _S("a_all", "adminp", "Barcha arizalar", "📋", "primary"),
    _S("a_users", "adminp", "Foydalanuvchilar", "👥", "primary"),
    _S("a_stats", "adminp", "Statistika", "📊", "success"),
    _S("a_settings", "adminp", "Sozlamalar", "⚙️", "primary"),
    _S("a_broadcast", "adminp", "Xabar yuborish", "📢", "success"),
    _S("a_export", "adminp", "CSV eksport", "📤", "primary"),
    # --- Ariza boshqaruvi
    _S("s_accept", "adminact", "Qabul qilish", "✅", "success"),
    _S("s_progress", "adminact", "Jarayonda", "🔄", "primary"),
    _S("s_done", "adminact", "Yakunlandi", "🏁", "success"),
    _S("s_reject", "adminact", "Rad etish", "❌", "danger"),
    _S("s_write", "adminact", "Mijozga yozish", "💬", "primary"),
    _S("s_detail", "adminact", "Batafsil ma'lumot", "📋", "primary"),
    _S("u_ban", "adminact", "Bloklash", "🚫", "danger"),
    _S("u_unban", "adminact", "Blokdan chiqarish", "✅", "success"),
    _S("u_orders", "adminact", "Arizalari", "📂", "primary"),
    _S("u_write", "adminact", "Xabar yozish", "💬", "primary"),
    _S("b_send", "adminact", "Yuborish", "🚀", "success"),
    # --- Sozlamalar
    _S("t_ui", "settings", "Tugmalarni tahrirlash", "🎨", "primary"),
    _S("t_wizard", "settings", "Premium emoji sozlash", "💎", "success"),
    _S("t_sub", "settings", "Majburiy obuna", "🔒", "primary"),
    _S("t_texts", "settings", "Bot matnlari", "📝", "primary"),
    _S("t_toggle", "settings", "Almashtirgich", "🔘", "primary"),
    _S("x_color", "settings", "Rangni o'zgartirish", "🎨", "primary"),
    _S("x_emoji", "settings", "Premium emoji belgilash", "💎", "success"),
    _S("x_text", "settings", "Matnni o'zgartirish", "✏️", "primary"),
    _S("x_reset", "settings", "Standartga qaytarish", "♻️", "danger"),
    _S("x_remove", "settings", "Emojini olib tashlash", "🗑", "danger"),
    _S("x_gcolor", "settings", "Guruhga rang berish", "🌈", "primary"),
    _S("x_wizard", "settings", "Ketma-ket sozlash", "🪄", "success"),
    # --- Majburiy obuna
    _S("sb_add", "sub", "Kanal qo'shish", "➕", "success"),
    _S("sb_del", "sub", "O'chirish", "🗑", "danger"),
    _S("sb_check", "sub", "Obunani tekshirish", "✅", "success"),
    _S("sb_join", "sub", "Kanalga o'tish", "📢", "primary"),
    # --- Holatlar (matn va tugma sifatida)
    _S("st_pending", "status", "Kutilmoqda", "🟡", None),
    _S("st_accepted", "status", "Qabul qilindi", "🟢", "success"),
    _S("st_in_progress", "status", "Jarayonda", "🔵", "primary"),
    _S("st_done", "status", "Yakunlandi", "🟣", "primary"),
    _S("st_rejected", "status", "Rad etildi", "🔴", "danger"),
    # --- Matnlardagi emojilar
    _S("em_new", "emoji", "Yangi buyurtma", "📥"),
    _S("em_user", "emoji", "Foydalanuvchi", "👤"),
    _S("em_phone", "emoji", "Telefon", "📞"),
    _S("em_id", "emoji", "ID", "🆔"),
    _S("em_loc", "emoji", "Joylashuv", "📍"),
    _S("em_bot", "emoji", "Bot", "🤖"),
    _S("em_cal", "emoji", "Sana", "📅"),
    _S("em_ok", "emoji", "Muvaffaqiyat", "✅"),
    _S("em_no", "emoji", "Rad / xato", "❌"),
    _S("em_warn", "emoji", "Ogohlantirish", "⚠️"),
    _S("em_info", "emoji", "Ma'lumot", "ℹ️"),
    _S("em_star", "emoji", "Yulduz", "✨"),
    _S("em_wave", "emoji", "Salom", "👋"),
    _S("em_list", "emoji", "Ro'yxat", "📋"),
    _S("em_chart", "emoji", "Statistika", "📊"),
    _S("em_lock", "emoji", "Qulf", "🔒"),
    _S("em_bell", "emoji", "Bildirishnoma", "🔔"),
    _S("em_edit", "emoji", "Tahrir", "✏️"),
    _S("em_msg", "emoji", "Xabar", "💬"),
    _S("em_rocket", "emoji", "Raketa", "🚀"),
    _S("em_clock", "emoji", "Kutish", "⏳"),
    _S("em_pin", "emoji", "Belgi", "📌"),
    _S("em_link", "emoji", "Havola", "🔗"),
    _S("em_file", "emoji", "Fayl", "📎"),
    _S("em_gear", "emoji", "Sozlama", "⚙️"),
    _S("em_ban", "emoji", "Bloklash", "🚫"),
    _S("em_target", "emoji", "Maqsad", "🎯"),
    _S("em_crown", "emoji", "Admin", "👑"),
    _S("em_palette", "emoji", "Dizayn", "🎨"),
    _S("em_gem", "emoji", "Premium", "💎"),
]

SLOTS: dict[str, Slot] = {s.key: s for s in SLOT_LIST}
assert len(SLOTS) == len(SLOT_LIST), "registry'da takrorlangan kalit bor"
MENU_KEYS = tuple(k for k in SLOTS if k.startswith("m_"))
STYLES = ("primary", "success", "danger")


def group_slots(group: str) -> list[Slot]:
    return [s for s in SLOT_LIST if s.group == group]
