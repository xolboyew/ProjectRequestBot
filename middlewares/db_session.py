from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.database import session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Har bir update uchun alohida DB sessiya; handler tugagach commit qilinadi."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        async with session_factory() as session:
            data["session"] = session
            result = await handler(event, data)
            await session.commit()
            return result
