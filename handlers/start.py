"""/start, bekor qilish va obunani tekshirish."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database.models import User
from handlers.registration import begin_registration
from keyboards.user import main_menu
from services import subscription
from services.settings_service import app_settings
from sqlalchemy.ext.asyncio import AsyncSession
from utils.filters import UIText
from utils.texts import e, esc, render

router = Router()


def welcome_text(user: User) -> str:
    return render(app_settings.get("welcome_text"), name=esc(user.first_name or user.tg_full_name, "do'stim"))


async def send_home(message: Message, user: User, is_admin: bool) -> None:
    await message.answer(welcome_text(user), reply_markup=main_menu(is_admin))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    await state.clear()
    if user.is_registered:
        await send_home(message, user, is_admin)
        return
    await message.answer(render(
        "{em_wave} <b>Xush kelibsiz!</b>\n\nBotdan foydalanish uchun avval qisqa ro'yxatdan o'tamiz "
        "— bor-yo'g'i 4 ta qadam {em_rocket}"), reply_markup=ReplyKeyboardRemove())
    await begin_registration(message, state)


@router.message(UIText("f_cancel"))
@router.message(Command("cancel"))
async def cancel_any(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    await state.clear()
    if user.is_registered:
        await message.answer(f"{e('em_no')} Bekor qilindi.", reply_markup=main_menu(is_admin))
    else:
        await message.answer("Ro'yxatdan o'tish uchun /start buyrug'ini yuboring.", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "sub:check")
async def check_subscription(cb: CallbackQuery, session: AsyncSession, user: User, is_admin: bool) -> None:
    missing = await subscription.missing_channels(session, cb.bot, cb.from_user.id, use_cache=False)
    if missing:
        await cb.answer("Hali hamma kanalga obuna bo'lmadingiz", show_alert=True)
        return
    await cb.answer("✅ Rahmat!")
    try:
        await cb.message.delete()
    except Exception:
        pass
    if user.is_registered:
        await cb.bot.send_message(cb.from_user.id, welcome_text(user), reply_markup=main_menu(is_admin))
    else:
        await cb.bot.send_message(cb.from_user.id, "Ro'yxatdan o'tish uchun /start buyrug'ini yuboring.")
