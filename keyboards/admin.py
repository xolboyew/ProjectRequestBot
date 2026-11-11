from __future__ import annotations

from keyboards.builder import ib, ikb, pager, raw_ib
from utils.constants import (ACCEPTED, DONE, IN_PROGRESS, REJECTED, STATUS_ACTION_SLOT, STATUS_SLOT,
                             STATUS_TITLE, STATUSES)
from utils.texts import fmt_date


def panel_kb(new_count: int = 0, orders: int = 0, users: int = 0):
    return ikb(
        [ib("a_new", "a:ol:new:0", suffix=f" ({new_count})"), ib("a_all", "a:ol:all:0", suffix=f" ({orders})")],
        [ib("a_users", "a:us:0", suffix=f" ({users})"), ib("a_stats", "a:st")],
        [ib("a_settings", "a:set"), ib("a_broadcast", "a:bc")],
        [ib("a_export", "a:exp")],
        [ib("n_close", "a:close")],
    )


def order_actions_kb(order, with_back: bool = True):
    status_btns = [ib(STATUS_ACTION_SLOT[s], f"a:s:{order.id}:{s}")
                   for s in (ACCEPTED, IN_PROGRESS, DONE, REJECTED) if s != order.status]
    rows = [status_btns[i:i + 2] for i in range(0, len(status_btns), 2)]
    rows.append([ib("s_write", f"a:w:{order.id}"), ib("s_detail", f"a:d:{order.id}")])
    if with_back:
        rows.append([ib("n_back", "a:ol:all:0", text="Ro'yxatga")])
    return ikb(*rows)


def orders_list_kb(orders, filter_key: str, page: int, pages: int):
    rows = []
    for o in orders:
        label = f"#{o.id} · {(o.bot_name or o.bot_type or 'Bot')[:16]} · {o.user.first_name or o.user.tg_full_name or ''}"[:48]
        rows.append([ib(STATUS_SLOT[o.status], f"a:ov:{o.id}", text=label)])
    rows.append(pager(f"a:ol:{filter_key}", page, pages))
    if filter_key in ("all",) or filter_key in STATUSES:
        chips = [ib("a_all", "a:ol:all:0", text="Hammasi")] + [
            ib(STATUS_SLOT[s], f"a:ol:{s}:0", text=STATUS_TITLE[s]) for s in STATUSES]
        rows += [chips[i:i + 2] for i in range(0, len(chips), 2)]
    rows.append([ib("n_back", "a:home")])
    return ikb(*rows)


def users_list_kb(users, page: int, pages: int):
    rows = []
    for u in users:
        mark = "🚫 " if u.is_banned else ""
        label = f"{mark}{u.full_name[:24]}" + (f" · @{u.username}" if u.username else "")
        rows.append([ib("em_user", f"a:u:{u.id}", text=label[:48])])
    rows.append(pager("a:us", page, pages))
    rows.append([ib("n_back", "a:home")])
    return ikb(*rows)


def user_card_kb(user):
    ban = ib("u_unban", f"a:unban:{user.id}") if user.is_banned else ib("u_ban", f"a:ban:{user.id}")
    return ikb(
        [ib("u_orders", f"a:ol:u{user.id}:0"), ib("u_write", f"a:wu:{user.id}")],
        [ban],
        [ib("n_back", "a:us:0")],
    )


def settings_kb(premium_on: bool, colors_on: bool):
    on, off = "yoqilgan", "o'chirilgan"
    return ikb(
        [ib("t_ui", "a:ui")],
        [ib("t_wizard", "a:uiw")],
        [ib("t_sub", "a:sub"), ib("t_texts", "a:tx")],
        [ib("t_toggle", "a:tg:premium", text=f"Premium emoji: {on if premium_on else off}",
            style="success" if premium_on else "danger")],
        [ib("t_toggle", "a:tg:colors", text=f"Tugma ranglari: {on if colors_on else off}",
            style="success" if colors_on else "danger")],
        [ib("n_back", "a:home")],
    )


def cancel_inline(cb: str = "a:cancel"):
    return ikb([ib("f_cancel", cb)])


def broadcast_confirm_kb():
    return ikb([ib("b_send", "a:bcgo")], [ib("f_cancel", "a:cancel")])


def admin_reply_kb(order_id: int, user_id: int):
    first = ib("s_write", f"a:w:{order_id}", text="Javob berish") if order_id else \
        ib("s_write", f"a:wu:{user_id}", text="Javob berish")
    rows = [[first]]
    if order_id:
        rows.append([ib("s_detail", f"a:ov:{order_id}", text="Arizani ochish")])
    return ikb(*rows)
