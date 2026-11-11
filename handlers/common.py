"""Boshqa hech qaysi handler ushlamagan xabar va tugmalar (eng oxirida ulanadi)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database.models import User
from keyboards.user import main_menu
from utils.texts import e

router = Router()


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery) -> None:
    await cb.answer()


@router.callback_query()
async def stale_callback(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan. Menyudan qayta tanlang.", show_alert=False)


@router.message()
async def fallback(message: Message, user: User, is_admin: bool) -> None:
    if not user.is_registered:
        await message.answer("Ro'yxatdan o'tish uchun /start buyrug'ini yuboring.")
        return
    await message.answer(f"{e('em_info')} Iltimos, pastdagi menyudan bo'limni tanlang.", reply_markup=main_menu(is_admin))
