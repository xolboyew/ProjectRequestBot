from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message, TelegramObject

from config import settings
from database.models import User
from services.ui import ui


class IsAdmin(BaseFilter):
    """Admin faqat .env / Secrets dagi ADMIN_IDS orqali aniqlanadi."""

    async def __call__(self, event: TelegramObject) -> bool:
        u = getattr(event, "from_user", None)
        return bool(u and u.id in settings.admin_ids)


class Registered(BaseFilter):
    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return bool(user and user.is_registered)


class UIText(BaseFilter):
    """Reply tugma bosilganda (admin matnni o'zgartirgan bo'lsa ham) to'g'ri ishlaydi."""

    def __init__(self, *keys: str) -> None:
        self.keys = keys

    async def __call__(self, message: Message) -> bool:
        return bool(message.text) and any(ui.matches(k, message.text) for k in self.keys)


class IsAnswer(BaseFilter):
    """Holatdagi (FSM) javob: buyruq ham, asosiy menyu tugmasi ham emas."""

    async def __call__(self, message: Message) -> bool:
        t = message.text
        if t is None:
            return True
        return not (t.startswith("/") or ui.is_menu_text(t))
