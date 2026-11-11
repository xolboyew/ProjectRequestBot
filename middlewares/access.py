from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings
from keyboards.user import sub_kb
from services import subscription
from services.order_service import get_or_create_user
from utils.texts import e

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    """Foydalanuvchini yuklaydi, bloklanganlarni to'xtatadi va majburiy obunani tekshiradi."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        chat = data.get("event_chat")
        if tg_user is None or tg_user.is_bot or (chat is not None and chat.type != "private"):
            return None

        session, bot = data["session"], data["bot"]
        user = await get_or_create_user(session, tg_user)
        is_admin = tg_user.id in settings.admin_ids
        data["user"], data["is_admin"] = user, is_admin

        if is_admin:
            return await handler(event, data)

        if user.is_banned:
            await self._reply(event, f"{e('em_ban')} Siz botdan foydalanishdan chetlatilgansiz.")
            return None

        is_check = isinstance(event, CallbackQuery) and event.data == "sub:check"
        if not is_check:
            missing = await subscription.missing_channels(session, bot, tg_user.id)
            if missing:
                text = (f"{e('em_lock')} <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling</b>\n\n"
                        f"Obuna bo'lgach, <b>Obunani tekshirish</b> tugmasini bosing.")
                if isinstance(event, CallbackQuery):
                    await event.answer("Avval kanallarga obuna bo'ling", show_alert=True)
                    await bot.send_message(tg_user.id, text, reply_markup=sub_kb(missing))
                elif isinstance(event, Message):
                    await event.answer(text, reply_markup=sub_kb(missing))
                return None
        return await handler(event, data)

    @staticmethod
    async def _reply(event: TelegramObject, text: str) -> None:
        try:
            if isinstance(event, CallbackQuery):
                await event.answer("Siz bloklangansiz", show_alert=True)
            elif isinstance(event, Message):
                await event.answer(text)
        except Exception as ex:  # pragma: no cover
            logger.debug("block reply failed: %s", ex)
