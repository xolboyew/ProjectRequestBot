"""Bot yaratish (ariza qoldirish), Arizalarim va Ariza holati."""
from __future__ import annotations

import re
from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.builder import ib, ikb
from keyboards.user import (confirm_kb, edit_fields_kb, main_menu, order_view_kb, orders_list_kb, question_kb,
                            status_kb)
from services import order_service as svc
from services.notifications import notify_admins_new_order
from services.ui import ui
from states.states import OrderFlow
from utils.constants import PAGE_SIZE, STATUSES, STATUS_TITLE
from utils.filters import IsAnswer, Registered, UIText
from utils.helpers import edit_or_send, extract_media
from utils.steps import MAX_FILES, MAX_TEXT, STEPS, TOTAL_STEPS
from utils.texts import e, order_summary, question_text, render, user_order_view

router = Router()
router.message.filter(Registered())
router.callback_query.filter(Registered())

USERNAME_RE = re.compile(r"^@[A-Za-z][A-Za-z0-9_]{2,29}[Bb][Oo][Tt]$")


# ============================================================ ariza qoldirish
async def ask(message: Message, idx: int) -> None:
    await message.answer(question_text(idx), reply_markup=question_kb(idx))


async def begin_order(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OrderFlow.question)
    await state.update_data(step=0, answers={}, files=[], editing=False)
    await message.answer(render(
        "{em_rocket} <b>Yangi ariza</b>\n\nBir nechta oddiy savolga javob bering. "
        "Istalgan payt <b>Orqaga</b> yoki <b>Bekor qilish</b> tugmalaridan foydalanishingiz mumkin."))
    await ask(message, 0)


@router.message(UIText("m_create"))
async def m_create(message: Message, state: FSMContext) -> None:
    await begin_order(message, state)


@router.callback_query(F.data == "u:new")
async def cb_new(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await begin_order(cb.message, state)


async def show_summary(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(OrderFlow.confirm)
    await state.update_data(editing=False)
    await message.answer(f"{e('em_ok')} <b>Barcha savollarga javob berildi!</b>", reply_markup=ReplyKeyboardRemove())
    await message.answer(order_summary(data["answers"], len(data["files"])), reply_markup=confirm_kb())


async def advance(message: Message, state: FSMContext, idx: int, editing: bool) -> None:
    if editing or idx + 1 >= TOTAL_STEPS:
        await show_summary(message, state)
    else:
        await state.update_data(step=idx + 1)
        await ask(message, idx + 1)


@router.message(OrderFlow.question, IsAnswer())
async def on_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    idx: int = data["step"]
    step = STEPS[idx]
    answers: dict = dict(data["answers"])
    files: list = list(data["files"])
    editing: bool = data.get("editing", False)
    raw = (message.text or "").strip()
    text = (message.text or message.caption or "").strip()

    # --- Orqaga
    if raw and ui.matches("f_back", raw):
        if editing:
            await show_summary(message, state)
        elif idx > 0:
            await state.update_data(step=idx - 1)
            await ask(message, idx - 1)
        else:
            await ask(message, idx)
        return

    # --- Tayyor (faqat ko'p xabarli savolda)
    if raw and step["kind"] == "multi" and ui.matches("f_done", raw):
        await advance(message, state, idx, editing)
        return

    # --- O'tkazib yuborish
    if raw and ui.matches("f_skip", raw):
        if step["required"]:
            await message.answer(f"{e('em_warn')} Bu savol majburiy, iltimos javob bering.")
            return
        answers[step["field"]] = "Aniq emas" if step["kind"] == "choice" else ""
        await state.update_data(answers=answers)
        await advance(message, state, idx, editing)
        return

    media = extract_media(message)
    if len(text) > MAX_TEXT:
        await message.answer(f"{e('em_warn')} Matn juda uzun (maksimum {MAX_TEXT} belgi). Qisqaroq yozing.")
        return
    if not text and not media:
        await message.answer(f"{e('em_warn')} Iltimos, matn yozing yoki fayl (rasm, video, hujjat) yuboring.")
        return

    # --- turiga qarab qiymat
    if step["kind"] == "username":
        if media or not text:
            await message.answer(f"{e('em_warn')} Username'ni matn ko'rinishida yozing. Masalan: <code>@MyProjectBot</code>")
            return
        uname = text if text.startswith("@") else f"@{text}"
        if not USERNAME_RE.match(uname):
            await message.answer(f"{e('em_warn')} Username noto'g'ri. U lotin harflarida, <b>bot</b> bilan tugashi va "
                                 f"kamida 5 belgidan iborat bo'lishi kerak. Masalan: <code>@MyProjectBot</code>")
            return
        value = uname
    elif step["kind"] == "choice":
        if ui.matches("f_yes", raw):
            value = "Ha, kerak"
        elif ui.matches("f_no", raw):
            value = "Yo'q, kerak emas"
        else:
            value = text
    else:
        value = text

    if media:
        if len(files) >= MAX_FILES:
            await message.answer(f"{e('em_warn')} Fayllar soni chegarasi ({MAX_FILES} ta) to'ldi.")
        else:
            files.append({**media, "caption": text or None, "step": idx})
        if not value:
            value = "📎 Fayl ilova qilindi"

    if step["kind"] == "multi":
        prev = answers.get(step["field"]) or ""
        answers[step["field"]] = (prev + "\n" + value).strip()
        await state.update_data(answers=answers, files=files)
        await message.answer(f"{e('em_ok')} Qabul qilindi. Yana yuborishingiz mumkin yoki <b>Tayyor</b> tugmasini bosing.")
        return

    answers[step["field"]] = value
    await state.update_data(answers=answers, files=files)
    await advance(message, state, idx, editing)


# ------------------------------------------------------------ tasdiqlash / tahrirlash
@router.message(OrderFlow.confirm, IsAnswer())
async def confirm_state_text(message: Message) -> None:
    await message.answer(f"{e('em_info')} Iltimos, yuqoridagi tugmalardan birini tanlang.")


@router.callback_query(OrderFlow.confirm, F.data == "ord:ok")
async def confirm_order(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User,
                        is_admin: bool) -> None:
    data = await state.get_data()
    await state.clear()  # ikki marta bosishdan himoya
    order = await svc.create_order(session, user, data["answers"], data["files"])
    await cb.answer("✅ Yuborildi")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.bot.send_message(cb.from_user.id, render(
        f"{{em_ok}} <b>Arizangiz qabul qilindi!</b>\n\n"
        f"{{em_id}} Ariza raqami: <b>#{order.id}</b>\n"
        f"{{em_pin}} Holati: " + "{st_pending} <b>Kutilmoqda</b>\n\n"
        "Admin tez orada siz bilan bog'lanadi. Holatni <b>Arizalarim</b> bo'limida kuzatib boring."),
        reply_markup=main_menu(is_admin))
    await notify_admins_new_order(cb.bot, order, user, data["files"])


@router.callback_query(OrderFlow.confirm, F.data == "ord:cancel")
async def cancel_order(cb: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    await state.clear()
    await cb.answer("Bekor qilindi")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.bot.send_message(cb.from_user.id, f"{e('em_no')} Ariza bekor qilindi.", reply_markup=main_menu(is_admin))


@router.callback_query(OrderFlow.confirm, F.data == "ord:edit")
async def edit_pick(cb: CallbackQuery) -> None:
    await cb.answer()
    await edit_or_send(cb, f"{e('em_edit')} <b>Qaysi maydonni o'zgartirmoqchisiz?</b>", edit_fields_kb())


@router.callback_query(OrderFlow.confirm, F.data == "ord:back")
async def edit_back(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await cb.answer()
    await edit_or_send(cb, order_summary(data["answers"], len(data["files"])), confirm_kb())


@router.callback_query(OrderFlow.confirm, F.data.startswith("ord:f:"))
async def edit_field(cb: CallbackQuery, state: FSMContext) -> None:
    idx = int(cb.data.split(":")[2])
    if not 0 <= idx < TOTAL_STEPS:
        await cb.answer()
        return
    data = await state.get_data()
    answers, files = dict(data["answers"]), list(data["files"])
    if STEPS[idx]["kind"] == "multi":
        answers[STEPS[idx]["field"]] = ""
        files = [f for f in files if f.get("step") != idx]
    await state.set_state(OrderFlow.question)
    await state.update_data(step=idx, editing=True, answers=answers, files=files)
    await cb.answer()
    await ask(cb.message, idx)


@router.callback_query(F.data.startswith("ord:"))
async def stale_order_callback(cb: CallbackQuery) -> None:
    await cb.answer("Bu ariza jarayoni eskirgan. «Bot yaratish» orqali qaytadan boshlang.", show_alert=True)


# ============================================================ Arizalarim
async def render_user_orders(session: AsyncSession, user: User, page: int):
    orders, total = await svc.list_orders(session, user_id=user.id, page=page)
    if total == 0:
        return (f"{e('em_list')} <b>Arizalarim</b>\n\nSizda hali ariza yo'q. Birinchi arizangizni qoldiring {e('em_rocket')}",
                ikb([ib("f_new", "u:new")]))
    pages = max(1, ceil(total / PAGE_SIZE))
    text = f"{e('em_list')} <b>Mening arizalarim</b> — jami {total} ta\n\nBatafsil ko'rish uchun arizani tanlang:"
    return text, orders_list_kb(orders, page, pages)


@router.message(UIText("m_orders"))
async def m_orders(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.clear()
    text, kb = await render_user_orders(session, user, 0)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("u:o:"))
async def orders_page(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    page = max(0, int(cb.data.split(":")[2]))
    text, kb = await render_user_orders(session, user, page)
    await cb.answer()
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data.startswith("u:ov:"))
async def order_view(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    _, _, oid, src = cb.data.split(":")
    order = await svc.get_order(session, int(oid))
    if order is None or order.user_id != user.id:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    history = await svc.order_history(session, order.id)
    await cb.answer()
    await edit_or_send(cb, user_order_view(order, history), order_view_kb(order.id, src))


# ============================================================ Ariza holati
async def render_status(session: AsyncSession, user: User):
    counts = await svc.user_status_counts(session, user.id)
    total = sum(counts.values())
    if total == 0:
        return (f"{e('em_chart')} <b>Ariza holati</b>\n\nSizda hali ariza yo'q.", ikb([ib("f_new", "u:new")]))
    lines = [f"{e('em_chart')} <b>Arizalar holati</b>\n", f"Jami arizalar: <b>{total}</b>\n"]
    for s in STATUSES:
        lines.append(f"{e('st_' + s)} {STATUS_TITLE[s]}: <b>{counts[s]}</b>")
    active = await svc.user_active_orders(session, user.id)
    if active:
        lines.append(f"\n{e('em_pin')} <b>Faol arizalaringiz</b> — batafsil ko'rish uchun tanlang:")
    return "\n".join(lines), status_kb(active)


@router.message(UIText("m_status"))
async def m_status(message: Message, state: FSMContext, session: AsyncSession, user: User) -> None:
    await state.clear()
    text, kb = await render_status(session, user)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "u:st")
async def status_cb(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    text, kb = await render_status(session, user)
    await cb.answer()
    await edit_or_send(cb, text, kb)
