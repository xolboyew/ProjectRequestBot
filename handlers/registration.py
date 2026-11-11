"""Ro'yxatdan o'tish: ism -> familiya -> telefon (request_contact) -> joylashuv (request_location)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from database.models import User, utcnow
from keyboards.user import location_kb, main_menu, phone_kb
from states.states import Reg
from utils.filters import IsAnswer, UIText
from utils.texts import e, render

router = Router()


def valid_name(t: str) -> bool:
    return 2 <= len(t) <= 50 and not any(ch.isdigit() for ch in t) and not t.startswith("/")


def cap(t: str) -> str:
    t = t.strip()
    return t[:1].upper() + t[1:]


async def begin_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(Reg.first_name)
    await message.answer(
        f"{e('em_user')} <b>1/4 · Ismingiz</b>\n\nIltimos, ismingizni yozing.\n<i>Masalan: Azizbek</i>",
        reply_markup=ReplyKeyboardRemove())


@router.message(Reg.first_name, F.text, IsAnswer())
async def reg_first_name(message: Message, state: FSMContext, user: User) -> None:
    name = message.text.strip()
    if not valid_name(name):
        await message.answer(f"{e('em_warn')} Ism 2–50 belgidan iborat bo'lib, raqamlarsiz bo'lishi kerak. Qayta yozing.")
        return
    user.first_name = cap(name)
    await state.set_state(Reg.last_name)
    await message.answer(f"{e('em_user')} <b>2/4 · Familiyangiz</b>\n\nEndi familiyangizni yozing.\n<i>Masalan: Xolboyev</i>")


@router.message(Reg.last_name, F.text, IsAnswer())
async def reg_last_name(message: Message, state: FSMContext, user: User) -> None:
    name = message.text.strip()
    if not valid_name(name):
        await message.answer(f"{e('em_warn')} Familiya 2–50 belgidan iborat bo'lib, raqamlarsiz bo'lishi kerak. Qayta yozing.")
        return
    user.last_name = cap(name)
    await state.set_state(Reg.phone)
    await message.answer(
        f"{e('em_phone')} <b>3/4 · Telefon raqamingiz</b>\n\n"
        f"Pastdagi <b>tugmani bosing</b> — raqamingiz avtomatik yuboriladi.", reply_markup=phone_kb())


@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext, user: User) -> None:
    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer(f"{e('em_warn')} Iltimos, faqat <b>o'zingizning</b> raqamingizni yuboring (tugma orqali).")
        return
    phone = contact.phone_number
    user.phone = phone if phone.startswith("+") else f"+{phone}"
    await state.set_state(Reg.location)
    await message.answer(
        f"{e('em_loc')} <b>4/4 · Joylashuvingiz</b>\n\n"
        f"Pastdagi tugmani bosib joylashuvingizni yuboring. Xohlamasangiz, o'tkazib yuborishingiz mumkin.\n"
        f"<i>Ma'lumotlar faqat buyurtmani bajarish uchun ishlatiladi.</i>", reply_markup=location_kb())


@router.message(Reg.phone, IsAnswer())
async def reg_phone_wrong(message: Message) -> None:
    await message.answer(f"{e('em_warn')} Raqamni yozmang — pastdagi <b>«Telefon raqamni yuborish»</b> tugmasini bosing.",
                         reply_markup=phone_kb())


async def finish_registration(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    user.is_registered = True
    user.registered_at = utcnow()
    await state.clear()
    await message.answer(render(
        "{em_ok} <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
        "Endi quyidagi menyudan foydalanib bot buyurtma berishingiz mumkin {em_rocket}"),
        reply_markup=main_menu(is_admin))


@router.message(Reg.location, F.location)
async def reg_location(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    user.latitude, user.longitude = message.location.latitude, message.location.longitude
    await finish_registration(message, state, user, is_admin)


@router.message(Reg.location, UIText("f_skip"))
async def reg_location_skip(message: Message, state: FSMContext, user: User, is_admin: bool) -> None:
    await finish_registration(message, state, user, is_admin)


@router.message(Reg.location, IsAnswer())
async def reg_location_wrong(message: Message) -> None:
    await message.answer(f"{e('em_warn')} Pastdagi <b>«Joylashuvni yuborish»</b> tugmasini bosing yoki o'tkazib yuboring.",
                         reply_markup=location_kb())
