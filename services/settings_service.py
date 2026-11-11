"""Kalit-qiymat sozlamalari (bazada saqlanadi, xotirada keshlanadi)."""
from __future__ import annotations

from sqlalchemy import select

from database.database import session_factory
from database.models import Setting

DEFAULTS: dict[str, str] = {
    "premium_on": "1",
    "colors_on": "1",
    "sub_enabled": "0",
    "contact_username": "",
    "welcome_text": (
        "{em_wave} <b>Assalomu alaykum, {name}!</b>\n\n"
        "{em_star} <b>Xolboyev Dev</b> botiga xush kelibsiz.\n\n"
        "Bu yerda o'zingizga kerakli Telegram botga buyurtma berishingiz, "
        "arizangiz holatini kuzatishingiz va admin bilan bevosita bog'lanishingiz mumkin.\n\n"
        "Quyidagi menyudan tanlang {em_rocket}"
    ),
    "about_text": (
        "{em_bot} <b>Xolboyev Dev — Telegram bot studiyasi</b>\n\n"
        "{em_target} Biz biznesingiz uchun zamonaviy va ishonchli Telegram botlar yaratamiz: "
        "do'kon, buyurtma, CRM, to'lov, admin panel va boshqa yechimlar.\n\n"
        "{em_ok} Arizani shu bot orqali qoldiring — admin siz bilan bog'lanadi va "
        "loyiha holatini bot orqali kuzatib borasiz."
    ),
    "contact_text": (
        "{em_phone} <b>Aloqa</b>\n\n"
        "{em_msg} Savol yoki taklifingiz bo'lsa, quyidagi tugma orqali adminga yozing — "
        "javob shu bot ichida keladi.\n"
        "{em_clock} Ish vaqti: har kuni 09:00 – 21:00"
    ),
}


class AppSettings:
    def __init__(self) -> None:
        self._data: dict[str, str] = dict(DEFAULTS)

    async def load(self) -> None:
        async with session_factory() as s:
            rows = (await s.execute(select(Setting))).scalars().all()
        self._data = {**DEFAULTS, **{r.key: r.value for r in rows}}

    def get(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)

    def get_bool(self, key: str) -> bool:
        return self._data.get(key, "0") in ("1", "true", "True")

    async def set(self, key: str, value: str) -> None:
        async with session_factory() as s:
            row = await s.get(Setting, key)
            if row is None:
                s.add(Setting(key=key, value=value))
            else:
                row.value = value
            await s.commit()
        self._data[key] = value

    async def reset(self, key: str) -> None:
        async with session_factory() as s:
            row = await s.get(Setting, key)
            if row is not None:
                await s.delete(row)
                await s.commit()
        self._data[key] = DEFAULTS.get(key, "")


app_settings = AppSettings()
