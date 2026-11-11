"""
UI menejeri: tugma matni, rangi (style) va premium emoji ID'lari.
Admin o'zgartirganda bazaga yoziladi va xotira keshi darhol yangilanadi.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import delete, select

from database.database import session_factory
from database.models import UIElement
from services.settings_service import app_settings
from utils.registry import MENU_KEYS, SLOTS, group_slots


@dataclass(frozen=True)
class El:
    key: str
    group: str
    label: str
    emoji: str            # oddiy (zaxira) emoji
    style: Optional[str]  # primary | success | danger | None
    emoji_id: Optional[str]
    emoji_char: Optional[str]


class UIManager:
    def __init__(self) -> None:
        self._over: dict[str, dict] = {}

    # ---- yuklash
    async def load(self) -> None:
        async with session_factory() as s:
            rows = (await s.execute(select(UIElement))).scalars().all()
        self._over = {
            r.key: {"text": r.text, "style": r.style, "emoji_id": r.emoji_id, "emoji_char": r.emoji_char}
            for r in rows
            if r.key in SLOTS
        }

    # ---- global kalitlar
    @property
    def premium_on(self) -> bool:
        return app_settings.get_bool("premium_on")

    @property
    def colors_on(self) -> bool:
        return app_settings.get_bool("colors_on")

    # ---- o'qish
    def el(self, key: str) -> El:
        slot = SLOTS[key]
        o = self._over.get(key, {})
        style = o.get("style")
        if style is None:
            style = slot.style
        elif style == "default":
            style = None
        return El(
            key=key,
            group=slot.group,
            label=o.get("text") or slot.label,
            emoji=slot.emoji,
            style=style,
            emoji_id=o.get("emoji_id"),
            emoji_char=o.get("emoji_char"),
        )

    def emoji_html(self, key: str) -> str:
        e = self.el(key)
        if e.emoji_id and self.premium_on:
            char = html.escape(e.emoji_char or e.emoji)
            return f'<tg-emoji emoji-id="{e.emoji_id}">{char}</tg-emoji>'
        return e.emoji

    def matches(self, key: str, text: str | None) -> bool:
        if not text:
            return False
        t = text.strip()
        e = self.el(key)
        slot = SLOTS[key]
        return t in {e.label, f"{e.emoji} {e.label}", slot.label, f"{slot.emoji} {slot.label}"}

    def is_menu_text(self, text: str | None) -> bool:
        return any(self.matches(k, text) for k in MENU_KEYS)

    # ---- yozish
    async def _update(self, key: str, **fields) -> None:
        async with session_factory() as s:
            row = await s.get(UIElement, key)
            if row is None:
                row = UIElement(key=key)
                s.add(row)
            for name, value in fields.items():
                setattr(row, name, value)
            await s.commit()
        self._over.setdefault(key, {}).update(fields)

    async def set_style(self, key: str, style: str) -> None:
        await self._update(key, style=style)

    async def set_text(self, key: str, text: str) -> None:
        await self._update(key, text=text)

    async def set_emoji(self, key: str, emoji_id: str, char: str | None) -> None:
        await self._update(key, emoji_id=emoji_id, emoji_char=char)

    async def clear_emoji(self, key: str) -> None:
        await self._update(key, emoji_id=None, emoji_char=None)

    async def set_group_style(self, group: str, style: str) -> None:
        for slot in group_slots(group):
            await self._update(slot.key, style=style)

    async def reset(self, key: str) -> None:
        async with session_factory() as s:
            await s.execute(delete(UIElement).where(UIElement.key == key))
            await s.commit()
        self._over.pop(key, None)


ui = UIManager()
