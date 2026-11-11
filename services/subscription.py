"""Majburiy obuna tekshiruvi."""
from __future__ import annotations

import logging
import time

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Channel
from services.settings_service import app_settings

logger = logging.getLogger(__name__)
_ok_until: dict[int, float] = {}
CACHE_SECONDS = 60


async def active_channels(session: AsyncSession) -> list[Channel]:
    return list((await session.scalars(select(Channel).where(Channel.is_active.is_(True)))).all())


async def missing_channels(session: AsyncSession, bot: Bot, user_id: int, use_cache: bool = True) -> list[Channel]:
    if not app_settings.get_bool("sub_enabled"):
        return []
    if use_cache and _ok_until.get(user_id, 0) > time.monotonic():
        return []
    missing: list[Channel] = []
    for ch in await active_channels(session):
        try:
            member = await bot.get_chat_member(ch.chat_id, user_id)
            status = getattr(member.status, "value", member.status)
            if status in ("left", "kicked") or (status == "restricted" and not getattr(member, "is_member", True)):
                missing.append(ch)
        except Exception as ex:  # bot kanalda admin emas / kanal topilmadi — foydalanuvchini to'smaymiz
            logger.warning("Obunani tekshirib bo'lmadi (%s): %s", ch.chat_id, ex)
    if not missing:
        _ok_until[user_id] = time.monotonic() + CACHE_SECONDS
    else:
        _ok_until.pop(user_id, None)
    return missing
