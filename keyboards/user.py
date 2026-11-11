from __future__ import annotations

from keyboards.builder import ib, ikb, pager, raw_ib, rb, rkb
from utils.constants import STATUS_SLOT, STATUS_TITLE, STATUSES
from utils.steps import STEPS
from utils.texts import fmt_date


def main_menu(is_admin: bool):
    rows = [
        [rb("m_create")],
        [rb("m_orders"), rb("m_status")],
        [rb("m_profile"), rb("m_contact")],
        [rb("m_about")],
    ]
    if is_admin:
        rows.append([rb("m_admin")])
    return rkb(*rows, placeholder="Bo'limni tanlang")


def phone_kb(with_cancel: bool = False):
    return rkb([rb("r_phone", contact=True)], [rb("f_cancel")] if with_cancel else [])


def location_kb(with_skip: bool = True, with_cancel: bool = False):
    return rkb([rb("r_location", location=True)],
               [rb("f_skip")] if with_skip else [],
               [rb("f_cancel")] if with_cancel else [])


def cancel_kb():
    return rkb([rb("f_cancel")])


def question_kb(idx: int):
    step = STEPS[idx]
    rows = []
    if step["kind"] == "choice":
        rows.append([rb("f_yes"), rb("f_no")])
    if step["kind"] == "multi":
        rows.append([rb("f_done")])
    elif not step["required"]:
        rows.append([rb("f_skip")])
    nav = ([rb("f_back")] if idx > 0 else []) + [rb("f_cancel")]
    rows.append(nav)
    return rkb(*rows, placeholder="Javobingizni yozing yoki fayl yuboring")


def confirm_kb():
    return ikb([ib("f_confirm", "ord:ok")], [ib("f_edit", "ord:edit"), ib("f_cancel", "ord:cancel")])


def edit_fields_kb():
    buttons = [ib("f_field", f"ord:f:{i}", text=s["label"]) for i, s in enumerate(STEPS)]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([ib("n_back", "ord:back")])
    return ikb(*rows)


def orders_list_kb(orders, page: int, pages: int):
    rows = []
    for o in orders:
        name = (o.bot_name or o.bot_type or "Bot")[:22]
        rows.append([ib(STATUS_SLOT[o.status], f"u:ov:{o.id}:{page}", text=f"#{o.id} · {name} · {fmt_date(o.created_at)[:5]}")])
    rows.append(pager("u:o", page, pages))
    rows.append([ib("f_new", "u:new")])
    return ikb(*rows)


def status_kb(active_orders):
    rows = []
    for o in active_orders:
        name = (o.bot_name or o.bot_type or "Bot")[:24]
        rows.append([ib(STATUS_SLOT[o.status], f"u:ov:{o.id}:s", text=f"#{o.id} · {name}")])
    rows.append([ib("f_new", "u:new")])
    return ikb(*rows)


def order_view_kb(order_id: int, src: str):
    back = "u:st" if src == "s" else f"u:o:{src}"
    return ikb([ib("o_contact", f"u:r:{order_id}")], [ib("n_back", back)])


def profile_kb():
    return ikb([ib("p_name", "p:name")], [ib("p_phone", "p:phone")], [ib("p_loc", "p:loc")])


def contact_kb(username: str = ""):
    rows = [[ib("c_write", "c:w")]]
    if username:
        rows.append([ib("c_tg", url=f"https://t.me/{username.lstrip('@')}")])
    return ikb(*rows)


def pick_order_kb(orders):
    rows = [[ib("c_general", "u:r:0")]]
    for o in orders:
        name = (o.bot_name or o.bot_type or "Bot")[:24]
        rows.append([ib(STATUS_SLOT[o.status], f"u:r:{o.id}", text=f"Ariza #{o.id} · {name}")])
    return ikb(*rows)


def reply_to_admin_kb(order_id: int):
    return ikb([ib("o_reply", f"u:r:{order_id}")])


def status_notice_kb(order_id: int):
    return ikb([ib("n_home", f"u:ov:{order_id}:s", text="Arizani ko'rish")], [ib("o_contact", f"u:r:{order_id}")])


def sub_kb(channels):
    rows = [[ib("sb_join", url=ch.url, text=ch.title[:40])] for ch in channels]
    rows.append([ib("sb_check", "sub:check")])
    return ikb(*rows)
