"""Admin va mijozlarga bildirishnoma yuborish."""
from __future__ import annotations

import logging

from aiogram import Bot

from config import settings
from keyboards.admin import order_actions_kb
from keyboards.user import status_notice_kb
from utils.constants import ACCEPTED, DONE, IN_PROGRESS, PENDING, REJECTED
from utils.helpers import send_file
from utils.texts import admin_order_card, e, status_line

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    PENDING: "Arizangiz ko'rib chiqish uchun navbatda.",
    ACCEPTED: "Arizangiz qabul qilindi! Tez orada admin siz bilan bog'lanadi.",
    IN_PROGRESS: "Arizangiz ustida ish boshlandi.",
    DONE: "Loyihangiz yakunlandi. Xizmatimizdan foydalanganingiz uchun rahmat!",
    REJECTED: "Afsuski, arizangiz rad etildi. Savollar bo'lsa, admin bilan bog'laning.",
}


async def notify_admins_new_order(bot: Bot, order, user, files) -> None:
    text = admin_order_card(order, user, new=True)
    kb = order_actions_kb(order, with_back=False)
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
            if user.latitude is not None and user.longitude is not None:
                await bot.send_location(admin_id, user.latitude, user.longitude)
            for f in files:
                await send_file(bot, admin_id, f["type"], f["file_id"], f.get("caption"))
        except Exception as ex:
            logger.warning("Adminga (%s) yangi ariza yuborilmadi: %s", admin_id, ex)


async def notify_user_status(bot: Bot, order, user, new_status: str) -> bool:
    text = (f"{e('em_bell')} <b>Ariza #{order.id} holati yangilandi</b>\n\n"
            f"Yangi holat: {status_line(new_status)}\n\n"
            f"{STATUS_MESSAGES.get(new_status, '')}")
    try:
        await bot.send_message(user.tg_id, text, reply_markup=status_notice_kb(order.id))
        return True
    except Exception as ex:
        logger.warning("Mijozga (%s) holat xabari yuborilmadi: %s", user.tg_id, ex)
        return False
