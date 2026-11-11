"""Aloqa, Bot haqida va mijoz -> admin xabarlari."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from keyboards.admin import admin_reply_kb
from keyboards.builder import ib, ikb
from keyboards.user import cancel_kb, contact_kb, main_menu, pick_order_kb
from services import order_service as svc
from services.settings_service import app_settings
from states.states import Contact
from utils.filters import IsAnswer, Registered, UIText
from utils.texts import e, esc, render, username_of

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(Registered())
router.callback_query.filter(Registered())


@router.message(UIText("m_contact"))
async def m_contact(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(render(app_settings.get("contact_text")),
                         reply_markup=contact_kb(app_settings.get("contact_username")))


@router.message(UIText("m_about"))
async def m_about(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(render(app_settings.get("about_text")), reply_markup=ikb([ib("f_new", "u:new")]))


@router.callback_query(F.data == "c:w")
async def choose_order(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    await cb.answer()
    orders, total = await svc.list_orders(session, user_id=user.id, page=0, size=5)
    if not orders:
        await start_write(cb.message, state, 0)
        return
    await cb.message.answer(f"{e('em_msg')} <b>Qaysi masala bo'yicha yozmoqchisiz?</b>", reply_markup=pick_order_kb(orders))


async def start_write(message: Message, state: FSMContext, order_id: int) -> None:
    await state.set_state(Contact.write)
    await state.update_data(order_id=order_id)
    target = f"Ariza #{order_id} bo'yicha" if order_id else "Umumiy savol"
    await message.answer(f"{e('em_edit')} <b>{target}</b>\n\nXabaringizni yozing (matn, rasm, hujjat yuborishingiz mumkin). "
                         f"Admin javobi shu bot ichida keladi.", reply_markup=cancel_kb())


@router.callback_query(F.data.startswith("u:r:"))
async def reply_to_admin(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User) -> None:
    order_id = int(cb.data.split(":")[2])
    if order_id:
        order = await svc.get_order(session, order_id)
        if order is None or order.user_id != user.id:
            await cb.answer("Ariza topilmadi", show_alert=True)
            return
    await cb.answer()
    await start_write(cb.message, state, order_id)


@router.message(Contact.write, IsAnswer())
async def send_to_admin(message: Message, state: FSMContext, session: AsyncSession, user: User,
                        is_admin: bool) -> None:
    data = await state.get_data()
    order_id: int = data.get("order_id", 0)
    if not (message.text or message.caption or message.photo or message.document or message.video or message.voice):
        await message.answer(f"{e('em_warn')} Matn yoki fayl yuboring.")
        return
    header = (f"{e('em_msg')} <b>Mijozdan xabar</b>\n"
              f"{e('em_user')} {esc(user.full_name)} · {username_of(user)} · <code>{user.tg_id}</code>\n"
              f"{e('em_id')} {'Ariza #' + str(order_id) if order_id else 'Umumiy savol'}")
    kb = admin_reply_kb(order_id, user.id)
    delivered = 0
    for admin_id in settings.admin_ids:
        try:
            if message.text:
                await message.bot.send_message(admin_id, f"{header}\n\n{esc(message.text)}", reply_markup=kb)
            else:
                await message.bot.send_message(admin_id, header)
                await message.copy_to(admin_id, reply_markup=kb)
            delivered += 1
        except Exception as ex:
            logger.warning("Adminga (%s) xabar yetkazilmadi: %s", admin_id, ex)
    await svc.save_message(session, user_id=user.id, order_id=order_id, direction="user_to_admin",
                           sender_tg_id=user.tg_id, text=message.text or message.caption or "[fayl]")
    await state.clear()
    if delivered:
        await message.answer(f"{e('em_ok')} Xabaringiz adminga yuborildi. Javob shu yerda keladi.",
                             reply_markup=main_menu(is_admin))
    else:
        await message.answer(f"{e('em_warn')} Xabarni yetkazib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.",
                             reply_markup=main_menu(is_admin))
