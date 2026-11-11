"""Admin -> mijoz xabarlari va ommaviy xabar yuborish."""
from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.admin import broadcast_confirm_kb, cancel_inline
from keyboards.user import reply_to_admin_kb
from services import order_service as svc
from states.states import AdminWrite, Broadcast
from utils.filters import IsAdmin, IsAnswer
from utils.texts import e, esc

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ============================================================ mijozga yozish
async def begin_write(cb: CallbackQuery, state: FSMContext, user: User, order_id: int) -> None:
    await cb.answer()
    await state.set_state(AdminWrite.message)
    await state.update_data(user_id=user.id, order_id=order_id)
    target = f"Ariza #{order_id}" if order_id else "Umumiy"
    await cb.message.answer(
        f"{e('em_msg')} <b>{target}</b> · {esc(user.full_name)}\n\nMijozga yuboriladigan xabarni yozing "
        f"(matn, rasm, hujjat…):", reply_markup=cancel_inline())


@router.callback_query(F.data.startswith("a:w:"))
async def write_for_order(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    order = await svc.get_order(session, int(cb.data.split(":")[2]))
    if order is None:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    await begin_write(cb, state, order.user, order.id)


@router.callback_query(F.data.startswith("a:wu:"))
async def write_for_user(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await svc.get_user(session, int(cb.data.split(":")[2]))
    if user is None:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    await begin_write(cb, state, user, 0)


@router.message(AdminWrite.message, IsAnswer())
async def send_to_user(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user = await svc.get_user(session, data["user_id"])
    order_id: int = data.get("order_id", 0)
    if user is None:
        await state.clear()
        await message.answer(f"{e('em_no')} Foydalanuvchi topilmadi.")
        return
    header = f"{e('em_msg')} <b>Admin xabari</b>" + (f" · Ariza #{order_id}" if order_id else "")
    kb = reply_to_admin_kb(order_id)
    try:
        if message.text:
            await message.bot.send_message(user.tg_id, f"{header}\n\n{message.html_text}", reply_markup=kb)
        else:
            await message.bot.send_message(user.tg_id, header)
            await message.copy_to(user.tg_id, reply_markup=kb)
    except Exception as ex:
        logger.warning("Mijozga (%s) xabar yetmadi: %s", user.tg_id, ex)
        await state.clear()
        await message.answer(f"{e('em_no')} Xabar yetkazilmadi (mijoz botni to'xtatgan bo'lishi mumkin).")
        return
    await svc.save_message(session, user_id=user.id, order_id=order_id, direction="admin_to_user",
                           sender_tg_id=message.from_user.id, text=message.text or message.caption or "[fayl]")
    await svc.log_admin_action(session, message.from_user.id, "message_to_user", f"user {user.tg_id}, order {order_id}")
    await state.clear()
    await message.answer(f"{e('em_ok')} Xabar mijozga yuborildi.")


# ============================================================ ommaviy xabar
@router.callback_query(F.data == "a:bc")
async def bc_start(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(Broadcast.content)
    await cb.message.answer(
        f"{e('em_bell')} <b>Ommaviy xabar</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yuboring "
        f"(matn, rasm, video, hujjat — premium emoji ham bo'ladi):", reply_markup=cancel_inline())


@router.message(Broadcast.content, IsAnswer())
async def bc_content(message: Message, state: FSMContext) -> None:
    await state.update_data(src_chat=message.chat.id, src_msg=message.message_id)
    await state.set_state(Broadcast.confirm)
    await message.answer(f"{e('em_info')} Xabar shunday ko'rinadi:")
    await message.copy_to(message.chat.id)
    await message.answer("Hammaga yuborilsinmi?", reply_markup=broadcast_confirm_kb())


async def _copy(bot, chat_id: int, src_chat: int, src_msg: int) -> bool:
    for _ in range(2):
        try:
            await bot.copy_message(chat_id, src_chat, src_msg)
            return True
        except TelegramRetryAfter as ex:
            await asyncio.sleep(ex.retry_after + 1)
        except Exception:
            return False
    return False


@router.callback_query(Broadcast.confirm, F.data == "a:bcgo")
async def bc_go(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()
    ids = await svc.all_user_tg_ids(session)
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    status = await cb.message.answer(f"{e('em_rocket')} Yuborilmoqda… 0/{len(ids)}")
    ok = failed = 0
    for i, tg_id in enumerate(ids, 1):
        if await _copy(cb.bot, tg_id, data["src_chat"], data["src_msg"]):
            ok += 1
        else:
            failed += 1
        if i % 25 == 0:
            try:
                await status.edit_text(f"{e('em_rocket')} Yuborilmoqda… {i}/{len(ids)}")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await svc.log_admin_action(session, cb.from_user.id, "broadcast", f"ok={ok} failed={failed}")
    await status.edit_text(f"{e('em_ok')} <b>Yuborish yakunlandi</b>\n\nMuvaffaqiyatli: <b>{ok}</b>\nYetmadi: <b>{failed}</b>")
