"""Tugma fabrikasi: tugma matni, rangi va premium emoji admin sozlamalaridan olinadi."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from services.ui import ui


def _kw(key: str, text: str | None = None, suffix: str = "", style: str | None = None) -> dict:
    el = ui.el(key)
    label = (text if text is not None else el.label) + suffix
    kw: dict = {}
    if el.emoji_id and ui.premium_on:
        kw["text"] = label
        kw["icon_custom_emoji_id"] = el.emoji_id
    else:
        kw["text"] = f"{el.emoji} {label}"
    st = style or el.style
    if st and st != "default" and ui.colors_on:
        kw["style"] = st
    return kw


def ib(key: str, cb: str | None = None, *, url: str | None = None, text: str | None = None,
       suffix: str = "", style: str | None = None) -> InlineKeyboardButton:
    return InlineKeyboardButton(**_kw(key, text, suffix, style), callback_data=cb, url=url)


def raw_ib(text: str, cb: str | None = None, *, url: str | None = None,
           style: str | None = None) -> InlineKeyboardButton:
    kw: dict = {"text": text}
    if style and style != "default":
        kw["style"] = style
    return InlineKeyboardButton(**kw, callback_data=cb, url=url)


def rb(key: str, *, contact: bool = False, location: bool = False, text: str | None = None) -> KeyboardButton:
    return KeyboardButton(**_kw(key, text), request_contact=True if contact else None,
                          request_location=True if location else None)


def ikb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows if r])


def rkb(*rows: list[KeyboardButton], placeholder: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[list(r) for r in rows if r], resize_keyboard=True,
                               input_field_placeholder=placeholder)


def pager(prefix: str, page: int, pages: int) -> list[InlineKeyboardButton]:
    if pages <= 1:
        return []
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(ib("n_prev", f"{prefix}:{page - 1}"))
    row.append(raw_ib(f"{page + 1}/{pages}", "noop"))
    if page < pages - 1:
        row.append(ib("n_next", f"{prefix}:{page + 1}"))
    return row
