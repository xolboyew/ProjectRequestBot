"""Barcha matnlar. Emoji'lar admin belgilagan premium emoji bilan almashadi."""
from __future__ import annotations

import html
import re
from datetime import timezone

from services.ui import ui
from utils.constants import STATUS_TITLE, STATUSES, TZ
from utils.registry import SLOTS
from utils.steps import STEPS, TOTAL_STEPS

_PLACEHOLDER = re.compile(r"\{((?:em|st)_[a-z_]+)\}")


def e(key: str) -> str:
    return ui.emoji_html(key)


def esc(value, dash: str = "—") -> str:
    s = str(value).strip() if value is not None else ""
    return html.escape(s) if s else dash


def cut(value, n: int = 350) -> str:
    s = str(value).strip() if value is not None else ""
    if not s:
        return "—"
    return html.escape(s[:n] + ("…" if len(s) > n else ""))


def render(template: str, **variables) -> str:
    out = _PLACEHOLDER.sub(lambda m: ui.emoji_html(m.group(1)) if m.group(1) in SLOTS else m.group(0), template)
    for k, v in variables.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def fmt_dt(dt) -> str:
    if not dt:
        return "—"
    return dt.replace(tzinfo=timezone.utc).astimezone(TZ).strftime("%d.%m.%Y %H:%M")


def fmt_date(dt) -> str:
    return dt.replace(tzinfo=timezone.utc).astimezone(TZ).strftime("%d.%m.%Y") if dt else "—"


def status_line(status: str) -> str:
    return f"{e('st_' + status)} <b>{STATUS_TITLE.get(status, status)}</b>"


def bar(done: int, total: int) -> str:
    return "▰" * done + "▱" * (total - done)


def username_of(user) -> str:
    return f"@{html.escape(user.username)}" if user.username else "—"


def maps_link(user) -> str:
    if user.latitude is None or user.longitude is None:
        return "—"
    return f'<a href="https://maps.google.com/?q={user.latitude},{user.longitude}">Xaritada ko\'rish</a>'


def question_text(idx: int) -> str:
    s = STEPS[idx]
    tail = "" if s["required"] else "\n<i>(ixtiyoriy — o'tkazib yuborishingiz mumkin)</i>"
    return (f"{e('em_bot')} <b>Savol {idx + 1}/{TOTAL_STEPS}</b>  {bar(idx + 1, TOTAL_STEPS)}\n\n"
            f"<b>{s['q']}</b>\n{s['hint']}{tail}")


def order_summary(answers: dict, files_count: int) -> str:
    lines = [f"{e('em_list')} <b>Arizangiz ma'lumotlari</b>\n"]
    for s in STEPS:
        lines.append(f"<b>{s['label']}:</b> {cut(answers.get(s['field']), 300)}")
    lines.append(f"{e('em_file')} <b>Biriktirilgan fayllar:</b> {files_count} ta")
    lines.append(f"\n{e('em_info')} Hammasi to'g'rimi? Tasdiqlang yoki tahrirlang.")
    return "\n".join(lines)


def admin_order_card(order, user, *, new: bool = False, full: bool = False) -> str:
    c = (lambda v: esc(v)) if full else (lambda v: cut(v))
    title = "YANGI BUYURTMA!" if new else f"ARIZA #{order.id}"
    head = e("em_new") if new else e("em_list")
    return (
        f"{head} <b>{title}</b>\n\n"
        f"{e('em_id')} <b>Ariza ID:</b> #{order.id}\n"
        f"{e('em_pin')} <b>Holati:</b> {status_line(order.status)}\n\n"
        f"{e('em_user')} <b>MIJOZ MA'LUMOTLARI:</b>\n"
        f"• Ism: {esc(user.first_name)}\n"
        f"• Familiya: {esc(user.last_name)}\n"
        f"• Telefon raqami: {esc(user.phone)}\n"
        f"• Telegram username: {username_of(user)}\n"
        f"• Telegram ID: <code>{user.tg_id}</code>\n"
        f"• Joylashuvi: {maps_link(user)}\n\n"
        f"{e('em_bot')} <b>LOYIHA MA'LUMOTLARI:</b>\n"
        f"• Bot nomi: {c(order.bot_name)}\n"
        f"• Bot username: {esc(order.bot_username)}\n"
        f"• Bot turi: {c(order.bot_type)}\n"
        f"• Bot vazifasi: {c(order.purpose)}\n"
        f"• Kerakli funksiyalar: {c(order.features)}\n"
        f"• Admin panel: {c(order.admin_panel)}\n"
        f"• Qo'shimcha talablar: {c(order.extra_requirements)}\n"
        f"• Qo'shimcha ma'lumot: {c(order.extra_info)}\n\n"
        f"{e('em_cal')} <b>Ariza yuborilgan vaqt:</b> {fmt_dt(order.created_at)}"
    )


def user_order_view(order, history) -> str:
    lines = [
        f"{e('em_bot')} <b>Ariza #{order.id}</b>",
        f"{e('em_pin')} Holati: {status_line(order.status)}",
        f"{e('em_cal')} Yuborilgan: {fmt_dt(order.created_at)}\n",
        f"<b>Bot turi:</b> {cut(order.bot_type, 300)}",
        f"<b>Bot nomi:</b> {cut(order.bot_name, 200)}",
        f"<b>Bot username:</b> {esc(order.bot_username)}",
        f"<b>Vazifasi:</b> {cut(order.purpose, 300)}",
        f"<b>Funksiyalar:</b> {cut(order.features, 300)}",
        f"<b>Admin panel:</b> {cut(order.admin_panel, 100)}",
        f"<b>Qo'shimcha talablar:</b> {cut(order.extra_requirements, 250)}",
        f"<b>Qo'shimcha ma'lumot:</b> {cut(order.extra_info, 250)}",
        f"\n{e('em_clock')} <b>Holat tarixi:</b>",
    ]
    for h in history[-8:]:
        lines.append(f"• {fmt_dt(h.created_at)} — {e('st_' + h.new_status)} {STATUS_TITLE.get(h.new_status, h.new_status)}")
    return "\n".join(lines)


def profile_text(user, orders_count: int) -> str:
    return (
        f"{e('em_user')} <b>Mening profilim</b>\n\n"
        f"• Ism va familiya: <b>{esc(user.first_name)} {esc(user.last_name, '')}</b>\n"
        f"• Telefon raqami: {esc(user.phone)}\n"
        f"• Telegram username: {username_of(user)}\n"
        f"• Telegram ID: <code>{user.tg_id}</code>\n"
        f"• Joylashuv: {maps_link(user)}\n"
        f"• Ro'yxatdan o'tgan sana: {fmt_date(user.registered_at)}\n"
        f"• Jami arizalar soni: <b>{orders_count}</b>"
    )


def user_card_admin(user, orders_count: int) -> str:
    return (
        f"{e('em_user')} <b>{esc(user.full_name)}</b>\n\n"
        f"• ID: <code>{user.tg_id}</code>\n"
        f"• Username: {username_of(user)}\n"
        f"• Telefon: {esc(user.phone)}\n"
        f"• Joylashuv: {maps_link(user)}\n"
        f"• Ro'yxatdan o'tgan: {'✅ ' + fmt_dt(user.registered_at) if user.is_registered else '❌ yo‘q'}\n"
        f"• Arizalar: <b>{orders_count}</b>\n"
        f"• Holati: {'🚫 bloklangan' if user.is_banned else '✅ faol'}"
    )


def stats_text(st: dict) -> str:
    lines = [
        f"{e('em_chart')} <b>Statistika</b>\n",
        f"{e('em_user')} <b>Foydalanuvchilar:</b> {st['users']} (ro'yxatdan o'tgan: {st['registered']}, "
        f"bloklangan: {st['banned']})",
        f"• Bugun qo'shilgan: {st['users_today']}\n",
        f"{e('em_list')} <b>Arizalar:</b> {st['orders']}",
        f"• Bugun: {st['orders_today']}",
        f"• So'nggi 7 kun: {st['orders_week']}\n",
        f"{e('em_pin')} <b>Holatlar bo'yicha:</b>",
    ]
    for s in STATUSES:
        lines.append(f"{e('st_' + s)} {STATUS_TITLE[s]}: <b>{st['by_status'][s]}</b>")
    return "\n".join(lines)
