from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


async def edit_or_send(cb: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    """Xabarni tahrirlaydi; imkoni bo'lmasa yangisini yuboradi."""
    msg = cb.message
    if isinstance(msg, Message):
        try:
            await msg.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest as ex:
            if "message is not modified" in str(ex):
                return
            logger.debug("edit_text bo'lmadi: %s", ex)
    await cb.bot.send_message(cb.from_user.id, text, reply_markup=kb)


def split_text(text: str, limit: int = 3900) -> list[str]:
    parts: list[str] = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        cut = cut if cut > limit // 2 else limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    parts.append(text)
    return parts


async def send_file(bot: Bot, chat_id: int, file_type: str, file_id: str, caption: str | None = None) -> None:
    senders = {
        "photo": bot.send_photo, "video": bot.send_video, "document": bot.send_document,
        "voice": bot.send_voice, "audio": bot.send_audio,
    }
    sender = senders.get(file_type, bot.send_document)
    await sender(chat_id, file_id, **({"caption": caption[:1000]} if caption else {}))


def extract_media(message: Message) -> dict | None:
    """Xabardagi rasm/video/hujjat/ovoz ma'lumotini qaytaradi."""
    if message.photo:
        return {"type": "photo", "file_id": message.photo[-1].file_id}
    if message.video:
        return {"type": "video", "file_id": message.video.file_id}
    if message.document:
        return {"type": "document", "file_id": message.document.file_id}
    if message.voice:
        return {"type": "voice", "file_id": message.voice.file_id}
    if message.audio:
        return {"type": "audio", "file_id": message.audio.file_id}
    return None


def extract_custom_emojis(message: Message) -> list[tuple[str, str]]:
    """Xabardan premium (custom) emoji ID va belgilarini ajratadi (tartib bilan)."""
    found: list[tuple[str, str]] = []
    if message.sticker and message.sticker.custom_emoji_id:
        found.append((message.sticker.custom_emoji_id, message.sticker.emoji or ""))
    source = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    for ent in sorted(entities, key=lambda e: e.offset):
        if ent.type == "custom_emoji" and ent.custom_emoji_id:
            found.append((ent.custom_emoji_id, ent.extract_from(source)))
    return found
