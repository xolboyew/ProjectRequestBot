"""Admin panel: arizalar, foydalanuvchilar, statistika, eksport."""
from __future__ import annotations

import csv
import io
from math import ceil

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from keyboards import admin as akb
from keyboards.builder import ib, ikb
from services import order_service as svc
from services.notifications import notify_user_status
from utils.constants import PAGE_SIZE, PENDING, STATUSES, STATUS_TITLE
from utils.filters import IsAdmin, UIText
from utils.helpers import edit_or_send, send_file, split_text
from utils.texts import admin_order_card, e, fmt_dt, stats_text, user_card_admin

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ============================================================ panel
async def panel(session: AsyncSession):
    st = await svc.get_stats(session)
    text = (f"{e('em_crown')} <b>Boshqaruv paneli</b>\n\n"
            f"{e('em_new')} Yangi arizalar: <b>{st['by_status'][PENDING]}</b>\n"
            f"{e('em_list')} Jami arizalar: <b>{st['orders']}</b>\n"
            f"{e('em_user')} Foydalanuvchilar: <b>{st['users']}</b>\n\n"
            f"Bo'limni tanlang:")
    return text, akb.panel_kb(st["by_status"][PENDING], st["orders"], st["users"])


@router.message(UIText("m_admin"))
@router.message(Command("admin"))
async def open_panel(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    text, kb = await panel(session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "a:home")
async def home(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await cb.answer()
    text, kb = await panel(session)
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data == "a:cancel")
async def cancel(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await cb.answer("Bekor qilindi")
    text, kb = await panel(session)
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data == "a:close")
async def close(cb: CallbackQuery) -> None:
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass


# ============================================================ arizalar ro'yxati
async def render_orders(session: AsyncSession, filter_key: str, page: int):
    status, user_id = None, None
    title = f"{e('em_list')} Barcha arizalar"
    if filter_key == "new":
        status, title = PENDING, f"{e('em_new')} Yangi arizalar"
    elif filter_key in STATUSES:
        status, title = filter_key, f"{e('st_' + filter_key)} {STATUS_TITLE[filter_key]}"
    elif filter_key.startswith("u") and filter_key[1:].isdigit():
        user_id = int(filter_key[1:])
        title = f"{e('em_user')} Foydalanuvchi arizalari"
    orders, total = await svc.list_orders(session, status=status, user_id=user_id, page=page)
    pages = max(1, ceil(total / PAGE_SIZE))
    if page >= pages:
        page = pages - 1
        orders, total = await svc.list_orders(session, status=status, user_id=user_id, page=page)
    body = "Hozircha bo'sh." if not total else "Arizani tanlang:"
    return f"{title} — <b>{total}</b> ta\n\n{body}", akb.orders_list_kb(orders, filter_key, page, pages)


@router.callback_query(F.data.startswith("a:ol:"))
async def orders_list(cb: CallbackQuery, session: AsyncSession) -> None:
    _, _, filter_key, page = cb.data.split(":")
    text, kb = await render_orders(session, filter_key, max(0, int(page)))
    await cb.answer()
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data.startswith("a:ov:"))
async def order_open(cb: CallbackQuery, session: AsyncSession) -> None:
    order = await svc.get_order(session, int(cb.data.split(":")[2]))
    if order is None:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    await cb.answer()
    await edit_or_send(cb, admin_order_card(order, order.user), akb.order_actions_kb(order))


@router.callback_query(F.data.startswith("a:s:"))
async def set_status(cb: CallbackQuery, session: AsyncSession) -> None:
    _, _, oid, status = cb.data.split(":")
    order = await svc.get_order(session, int(oid))
    if order is None or status not in STATUSES:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    if order.status == status:
        await cb.answer("Ariza allaqachon shu holatda")
        return
    await svc.change_status(session, order, status, cb.from_user.id)
    delivered = await notify_user_status(cb.bot, order, order.user, status)
    await cb.answer("✅ Holat yangilandi" + ("" if delivered else " (mijozga xabar yetmadi)"), show_alert=not delivered)
    await edit_or_send(cb, admin_order_card(order, order.user), akb.order_actions_kb(order))


@router.callback_query(F.data.startswith("a:d:"))
async def order_detail(cb: CallbackQuery, session: AsyncSession) -> None:
    order = await svc.get_order(session, int(cb.data.split(":")[2]))
    if order is None:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    await cb.answer()
    history = await svc.order_history(session, order.id)
    lines = [admin_order_card(order, order.user, full=True), f"\n{e('em_clock')} <b>Holat tarixi:</b>"]
    for h in history:
        who = "mijoz" if h.changed_by == order.user.tg_id else f"admin {h.changed_by}"
        lines.append(f"• {fmt_dt(h.created_at)} — {e('st_' + h.new_status)} {STATUS_TITLE.get(h.new_status, h.new_status)} ({who})")
    for part in split_text("\n".join(lines)):
        await cb.message.answer(part)
    u = order.user
    if u.latitude is not None and u.longitude is not None:
        await cb.message.answer_location(u.latitude, u.longitude)
    for f in await svc.order_files(session, order.id):
        try:
            await send_file(cb.bot, cb.from_user.id, f.file_type, f.file_id, f.caption)
        except Exception:
            await cb.message.answer(f"{e('em_warn')} Fayl yuborilmadi (fayl eskirgan bo'lishi mumkin).")


# ============================================================ foydalanuvchilar
@router.callback_query(F.data.startswith("a:us:"))
async def users_page(cb: CallbackQuery, session: AsyncSession) -> None:
    page = max(0, int(cb.data.split(":")[2]))
    users, total, size = await svc.list_users(session, page)
    pages = max(1, ceil(total / size))
    await cb.answer()
    await edit_or_send(cb, f"{e('em_user')} <b>Foydalanuvchilar</b> — {total} ta\n\nBatafsil ko'rish uchun tanlang:",
                       akb.users_list_kb(users, page, pages))


async def show_user(cb: CallbackQuery, session: AsyncSession, user_id: int) -> None:
    user = await svc.get_user(session, user_id)
    if user is None:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    count = await svc.user_orders_count(session, user.id)
    await edit_or_send(cb, user_card_admin(user, count), akb.user_card_kb(user))


@router.callback_query(F.data.startswith("a:u:"))
async def user_open(cb: CallbackQuery, session: AsyncSession) -> None:
    await cb.answer()
    await show_user(cb, session, int(cb.data.split(":")[2]))


@router.callback_query(F.data.startswith("a:ban:") | F.data.startswith("a:unban:"))
async def ban_toggle(cb: CallbackQuery, session: AsyncSession) -> None:
    _, action, uid = cb.data.split(":")
    user = await svc.get_user(session, int(uid))
    if user is None:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    if user.tg_id in settings.admin_ids:
        await cb.answer("Adminni bloklab bo'lmaydi", show_alert=True)
        return
    user.is_banned = action == "ban"
    await svc.log_admin_action(session, cb.from_user.id, action, f"user {user.tg_id}")
    await cb.answer("🚫 Bloklandi" if user.is_banned else "✅ Blokdan chiqarildi")
    await show_user(cb, session, user.id)


# ============================================================ statistika va eksport
@router.callback_query(F.data == "a:st")
async def stats(cb: CallbackQuery, session: AsyncSession) -> None:
    st = await svc.get_stats(session)
    await cb.answer()
    await edit_or_send(cb, stats_text(st), ikb([ib("n_back", "a:home")]))


def _safe(v) -> str:
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


@router.callback_query(F.data == "a:exp")
async def export_csv(cb: CallbackQuery, session: AsyncSession) -> None:
    await cb.answer("Tayyorlanmoqda…")
    orders = await svc.export_rows(session)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ID", "Holat", "Sana", "Ism", "Familiya", "Telefon", "Username", "Telegram ID", "Bot turi",
                "Bot nomi", "Bot username", "Vazifa", "Funksiyalar", "Admin panel", "Qo'shimcha talablar",
                "Qo'shimcha ma'lumot"])
    for o in orders:
        u = o.user
        w.writerow([o.id, STATUS_TITLE.get(o.status, o.status), fmt_dt(o.created_at), _safe(u.first_name),
                    _safe(u.last_name), _safe(u.phone), _safe(u.username), u.tg_id, _safe(o.bot_type),
                    _safe(o.bot_name), _safe(o.bot_username), _safe(o.purpose), _safe(o.features),
                    _safe(o.admin_panel), _safe(o.extra_requirements), _safe(o.extra_info)])
    await svc.log_admin_action(session, cb.from_user.id, "export_csv", f"{len(orders)} ta")
    await cb.message.answer_document(BufferedInputFile(buf.getvalue().encode("utf-8-sig"), filename="arizalar.csv"),
                                     caption=f"{e('em_ok')} Jami {len(orders)} ta ariza")
