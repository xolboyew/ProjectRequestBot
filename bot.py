"""Xolboyev Dev — Telegram CRM-bot. Ishga tushirish: python bot.py"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent

from config import settings
from database.database import init_db
from handlers import (admin, admin_comm, admin_settings, admin_ui, common, contact, orders, profile,
                      registration, start)
from middlewares.access import AccessMiddleware
from middlewares.db_session import DbSessionMiddleware
from services.settings_service import app_settings
from services.ui import ui
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def on_error(event: ErrorEvent) -> bool:
    logger.exception("Update ishlov berishda xatolik", exc_info=event.exception)
    update = event.update
    try:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.", show_alert=True)
        elif update.message:
            await update.message.answer("⚠️ Kutilmagan xatolik yuz berdi. Iltimos, /start ni bosing.")
    except Exception:
        pass
    return True


async def start_health_server(port: int) -> None:
    """Render/Railway 'web service' rejimida port ochiq bo'lishi uchun (ixtiyoriy)."""
    from aiohttp import web

    async def ok(_request: web.Request) -> web.Response:
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logger.info("Health server port %s da ishlamoqda", port)


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command="start", description="Botni boshlash"),
                               BotCommand(command="cancel", description="Joriy amalni bekor qilish")])
    for admin_id in settings.admin_ids:
        try:
            await bot.set_my_commands(
                [BotCommand(command="start", description="Botni boshlash"),
                 BotCommand(command="admin", description="Boshqaruv paneli"),
                 BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
                 BotCommand(command="premium_off", description="Premium emojini o'chirish"),
                 BotCommand(command="premium_on", description="Premium emojini yoqish")],
                scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as ex:  # admin hali botni /start qilmagan bo'lishi mumkin
            logger.info("Admin (%s) uchun buyruqlar o'rnatilmadi: %s", admin_id, ex)


async def main() -> None:
    setup_logging()
    await init_db()
    await app_settings.load()
    await ui.load()

    bot = Bot(token=settings.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
    dp = Dispatcher(storage=MemoryStorage())

    session_mw, access_mw = DbSessionMiddleware(), AccessMiddleware()
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(session_mw)
        observer.outer_middleware(access_mw)

    dp.include_routers(start.router, registration.router, admin.router, admin_comm.router,
                       admin_settings.router, admin_ui.router, orders.router, profile.router,
                       contact.router, common.router)
    dp.errors.register(on_error)

    if settings.port:
        await start_health_server(settings.port)

    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s | adminlar: %s | baza: %s", me.username, len(settings.admin_ids),
                settings.database_url.split("://")[0])
    await setup_commands(bot)
    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
