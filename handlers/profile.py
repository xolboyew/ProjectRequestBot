"""Mening profilim va ma'lumotlarni yangilash."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.user import cancel_kb, location_kb, main_menu, phone_kb, profile_kb
from services import order_service as svc
from states.states import ProfileEdit
from utils.filters import IsAnswer, Registered, UIText
from utils.texts import e, profile_text

router = Router()
router.message.filter(Registered())
router.callback_query.filter(Registered())


@router.message(UIText("m_profile"))
async def m_profile(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.clear()
    count = await svc.user_orders_count(session, user.id)
    await message.answer(profile_text(user, count), reply_markup=profile_kb())


# ---------------------------------------------------------------- ism-familiya
@router.callback_query(F.data == "p:name")
async def edit_name(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(ProfileEdit.name)
    await cb.message.answer(f"{e('em_edit')} Yangi <b>ism va familiyangizni</b> bitta xabarda yozing.\n"
                            f"<i>Masalan: Azizbek Xolboyev</i>", reply_markup=cancel_kb())


@router.message(ProfileEdit.name, F.text, IsAnswer())
async def save_name(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    parts = message.text.split()
    if len(parts) < 2 or any(ch.isdigit() for ch in message.text) or len(message.text) > 100:
        await message.answer(f"{e('em_warn')} Ism va familiyani birga yozing (raqamsiz). Masalan: <i>Azizbek Xolboyev</i>")
        return
    user.first_name = parts[0][:1].upper() + parts[0][1:]
    user.last_name = " ".join(parts[1:])[:1].upper() + " ".join(parts[1:])[1:]
    await state.clear()
    await message.answer(f"{e('em_ok')} Ism-familiya yangilandi.", reply_markup=main_menu(is_admin))


# ---------------------------------------------------------------- telefon
@router.callback_query(F.data == "p:phone")
async def edit_phone(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(ProfileEdit.phone)
    await cb.message.answer(f"{e('em_phone')} Pastdagi tugmani bosib yangi telefon raqamingizni yuboring.",
                            reply_markup=phone_kb(with_cancel=True))


@router.message(ProfileEdit.phone, F.contact)
async def save_phone(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    c = message.contact
    if c.user_id and c.user_id != message.from_user.id:
        await message.answer(f"{e('em_warn')} Faqat o'zingizning raqamingizni yuboring.")
        return
    user.phone = c.phone_number if c.phone_number.startswith("+") else f"+{c.phone_number}"
    await state.clear()
    await message.answer(f"{e('em_ok')} Telefon raqami yangilandi: <b>{user.phone}</b>", reply_markup=main_menu(is_admin))


@router.message(ProfileEdit.phone, IsAnswer())
async def phone_wrong(message: Message) -> None:
    await message.answer(f"{e('em_warn')} Raqamni yozmang — pastdagi tugmani bosing.", reply_markup=phone_kb(with_cancel=True))


# ---------------------------------------------------------------- joylashuv
@router.callback_query(F.data == "p:loc")
async def edit_loc(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(ProfileEdit.location)
    await cb.message.answer(f"{e('em_loc')} Pastdagi tugmani bosib joylashuvingizni yuboring.",
                            reply_markup=location_kb(with_skip=False, with_cancel=True))


@router.message(ProfileEdit.location, F.location)
async def save_loc(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    user.latitude, user.longitude = message.location.latitude, message.location.longitude
    await state.clear()
    await message.answer(f"{e('em_ok')} Joylashuv yangilandi.", reply_markup=main_menu(is_admin))


@router.message(ProfileEdit.location, IsAnswer())
async def loc_wrong(message: Message) -> None:
    await message.answer(f"{e('em_warn')} Pastdagi «Joylashuvni yuborish» tugmasini bosing.",
                         reply_markup=location_kb(with_skip=False, with_cancel=True))
