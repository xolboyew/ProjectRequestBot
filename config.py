"""Sozlamalar. Maxfiy qiymatlar faqat muhit o'zgaruvchilaridan (Secrets/Variables yoki .env) olinadi."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # faqat lokal ishlash uchun; hostingda Variables/Secrets ishlatiladi


def _parse_ids(raw: str) -> tuple[int, ...]:
    ids: list[int] = []
    for part in raw.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.append(int(part))
    return tuple(dict.fromkeys(ids))


def _db_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        (BASE_DIR / "data").mkdir(exist_ok=True)
        return f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}"
    if raw.startswith("postgres://"):
        return "postgresql+asyncpg://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw[len("postgresql://"):]
    return raw


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: tuple[int, ...]
    database_url: str
    log_level: str
    log_dir: Path
    port: int | None


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    admins = _parse_ids(os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "")))
    if not token:
        sys.exit("❌ BOT_TOKEN topilmadi. Hosting Variables/Secrets yoki .env faylga BOT_TOKEN yozing.")
    if not admins:
        sys.exit("❌ ADMIN_IDS topilmadi. Kamida bitta admin Telegram ID kiriting (masalan: 111111111).")
    port_raw = os.getenv("PORT", "").strip()
    return Settings(
        bot_token=token,
        admin_ids=admins,
        database_url=_db_url(os.getenv("DATABASE_URL", "")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_dir=BASE_DIR / "logs",
        port=int(port_raw) if port_raw.isdigit() else None,
    )


settings = load_settings()
