"""
Admin uchun dizayn markazi:
  • har bir tugmaning rangini (ko'k / yashil / qizil / rangsiz) o'zgartirish
  • har bir tugma va matn emojisiga premium emoji belgilash
  • tugma matnini tahrirlash, standartga qaytarish
  • guruh bo'yicha rang berish va ketma-ket (wizard) premium emoji sozlash
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.builder import ib, ikb, pager, raw_ib
from services.order_service import log_admin_action
from services.settings_service import app_settings
from services.ui import ui
from states.states import UIEdit
from utils.filters import IsAdmin, IsAnswer
from utils.helpers import edit_or_send, extract_custom_emojis
from utils.registry import GROUPS, SLOT_LIST, SLOTS, group_slots
from utils.texts import e, esc

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

COLOR_NAME = {"primary": "🔵 Ko'k", "success": "🟢 Yashil", "danger": "🔴 Qizil", None: "⚪ Rangsiz"}
PER_PAGE = 12


def text_editable(key: str) -> bool:
    return not key.startswith(("em_", "st_"))


# ============================================================ favqulodda buyruqlar
@router.message(Command("premium_off"))
async def premium_off(message: Message) -> None:
    await app_settings.set("premium_on", "0")
    await message.answer("Premium emoji O'CHIRILDI (oddiy emoji ishlatiladi). Qayta yoqish: /premium_on")


@router.message(Command("premium_on"))
async def premium_on(message: Message) -> None:
    await app_settings.set("premium_on", "1")
    await message.answer("Premium emoji YOQILDI. Muammo bo'lsa: /premium_off")


@router.message(Command("colors_off"))
async def colors_off(message: Message) -> None:
    await app_settings.set("colors_on", "0")
    await message.answer("Tugma ranglari O'CHIRILDI. Qayta yoqish: /colors_on")


@router.message(Command("colors_on"))
async def colors_on(message: Message) -> None:
    await app_settings.set("colors_on", "1")
    await message.answer("Tugma ranglari YOQILDI. Muammo bo'lsa: /colors_off")


# ============================================================ bosh sahifa va guruhlar
@router.callback_query(F.data == "a:ui")
async def ui_home(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    rows = [[raw_ib(title, f"a:uig:{g}:0", style="primary")] for g, title in GROUPS.items()]
    rows.append([ib("x_wizard", "a:uiw", text="Premium emojilarni ketma-ket sozlash")])
    rows.append([ib("n_back", "a:set")])
    text = (f"{e('em_palette')} <b>Tugma dizayni</b>\n\n"
            f"Guruhni tanlang, so'ng tugmani bosib uning <b>rangi</b>, <b>matni</b> va <b>premium emojisini</b> o'zgartiring.\n\n"
            f"💎 Premium emoji: {'✅ yoqilgan' if ui.premium_on else '❌ o‘chirilgan'}\n"
            f"🎨 Ranglar: {'✅ yoqilgan' if ui.colors_on else '❌ o‘chirilgan'}\n\n"
            f"<i>Tugmalar ro'yxatida har bir tugma hozirgi ko'rinishida chiqadi.</i>")
    await edit_or_send(cb, text, ikb(*rows))


@router.callback_query(F.data.startswith("a:uig:"))
async def group_view(cb: CallbackQuery) -> None:
    _, _, group, page = cb.data.split(":")
    if group not in GROUPS:
        await cb.answer()
        return
    page = max(0, int(page))
    slots = group_slots(group)
    pages = max(1, -(-len(slots) // PER_PAGE))
    page = min(page, pages - 1)
    chunk = slots[page * PER_PAGE:(page + 1) * PER_PAGE]
    buttons = [ib(s.key, f"a:uie:{s.key}", text=ui.el(s.key).label if not s.key.startswith("em_") else s.label)
               for s in chunk]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append(pager(f"a:uig:{group}", page, pages))
    rows.append([ib("x_gcolor", f"a:uigc:{group}"), ib("x_wizard", f"a:uiw:{group}")])
    rows.append([ib("n_back", "a:ui")])
    await cb.answer()
    await edit_or_send(cb, f"<b>{GROUPS[group]}</b>\n\nSozlamoqchi bo'lgan tugmani tanlang:", ikb(*rows))


# ============================================================ bitta tugma
def editor_text(key: str) -> str:
    el = ui.el(key)
    return (f"{e('em_palette')} <b>Tugma sozlamalari</b>\n\n"
            f"🔑 Kalit: <code>{key}</code>\n"
            f"🏷 Matn: <b>{esc(el.label)}</b>\n"
            f"🎨 Rang: {COLOR_NAME.get(el.style)}\n"
            f"💎 Premium emoji: {'✅ belgilangan' if el.emoji_id else '❌ yo‘q (oddiy emoji)'}\n"
            f"👁 Ko'rinishi: {ui.emoji_html(key)} {esc(el.label)}")


def editor_kb(key: str):
    el = ui.el(key)
    rows = [[ib("x_color", f"a:uic:{key}"), ib("x_emoji", f"a:uim:{key}")]]
    if text_editable(key):
        rows.append([ib("x_text", f"a:uit:{key}")])
    if el.emoji_id:
        rows.append([ib("x_remove", f"a:uimx:{key}")])
    rows.append([ib("x_reset", f"a:uir:{key}")])
    rows.append([ib("n_back", f"a:uig:{SLOTS[key].group}:0")])
    return ikb(*rows)


@router.callback_query(F.data.startswith("a:uie:"))
async def editor(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":")[2]
    if key not in SLOTS:
        await cb.answer()
        return
    await state.clear()
    await cb.answer()
    await edit_or_send(cb, editor_text(key), editor_kb(key))


# ---- rang
@router.callback_query(F.data.startswith("a:uic:"))
async def color_pick(cb: CallbackQuery) -> None:
    key = cb.data.split(":")[2]
    if key not in SLOTS:
        await cb.answer()
        return
    await cb.answer()
    kb = ikb(
        [raw_ib("🔵 Ko'k", f"a:uics:{key}:primary", style="primary"),
         raw_ib("🟢 Yashil", f"a:uics:{key}:success", style="success")],
        [raw_ib("🔴 Qizil", f"a:uics:{key}:danger", style="danger"),
         raw_ib("⚪ Rangsiz", f"a:uics:{key}:default")],
        [ib("n_back", f"a:uie:{key}")],
    )
    await edit_or_send(cb, f"{e('em_palette')} <b>{esc(ui.el(key).label)}</b> uchun rangni tanlang:", kb)


@router.callback_query(F.data.startswith("a:uics:"))
async def color_set(cb: CallbackQuery, session: AsyncSession) -> None:
    _, _, key, style = cb.data.split(":")
    if key not in SLOTS or style not in ("primary", "success", "danger", "default"):
        await cb.answer()
        return
    await ui.set_style(key, style)
    await log_admin_action(session, cb.from_user.id, "ui_color", f"{key}={style}")
    await cb.answer("🎨 Rang saqlandi")
    await edit_or_send(cb, editor_text(key), editor_kb(key))


# ---- premium emoji
@router.callback_query(F.data.startswith("a:uim:"))
async def emoji_start(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":")[2]
    if key not in SLOTS:
        await cb.answer()
        return
    await cb.answer()
    await state.set_state(UIEdit.emoji)
    await state.update_data(key=key)
    await cb.message.answer(
        f"{e('em_gem')} <b>{esc(ui.el(key).label)}</b> uchun premium emoji yuboring.\n\n"
        f"Shunchaki xabar ichida <b>premium emoji</b> yuboring (yoki emoji ID raqamini yozing).",
        reply_markup=ikb([ib("f_cancel", f"a:uie:{key}", text="Bekor qilish")]))


@router.message(UIEdit.emoji, IsAnswer())
async def emoji_receive(message: Message, state: FSMContext, session: AsyncSession) -> None:
    key = (await state.get_data()).get("key")
    found = extract_custom_emojis(message)
    raw = (message.text or "").strip()
    if not found and raw.isdigit() and 10 <= len(raw) <= 30:
        try:
            stickers = await message.bot.get_custom_emoji_stickers([raw])
        except Exception:
            stickers = []
        if stickers:
            found = [(raw, stickers[0].emoji or "")]
    if not found:
        await message.answer(f"{e('em_warn')} Xabarda premium emoji topilmadi. Premium emoji yuboring "
                             f"(oddiy emoji emas) yoki haqiqiy emoji ID'sini yozing.")
        return
    emoji_id, char = found[0]
    await ui.set_emoji(key, emoji_id, char)
    await log_admin_action(session, message.from_user.id, "ui_emoji", f"{key}={emoji_id}")
    await state.clear()
    await message.answer(f"{e('em_ok')} Premium emoji saqlandi!\n\n{editor_text(key)}", reply_markup=editor_kb(key))


@router.callback_query(F.data.startswith("a:uimx:"))
async def emoji_remove(cb: CallbackQuery) -> None:
    key = cb.data.split(":")[2]
    if key in SLOTS:
        await ui.clear_emoji(key)
    await cb.answer("🗑 Olib tashlandi")
    await edit_or_send(cb, editor_text(key), editor_kb(key))


# ---- matn
@router.callback_query(F.data.startswith("a:uit:"))
async def text_start(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":")[2]
    if key not in SLOTS or not text_editable(key):
        await cb.answer("Bu element uchun matn o'zgartirilmaydi", show_alert=True)
        return
    await cb.answer()
    await state.set_state(UIEdit.text)
    await state.update_data(key=key)
    await cb.message.answer(
        f"{e('em_edit')} Tugma uchun yangi matnni yuboring (emojisiz, 1–32 belgi).\nHozirgi: <b>{esc(ui.el(key).label)}</b>",
        reply_markup=ikb([ib("f_cancel", f"a:uie:{key}", text="Bekor qilish")]))


@router.message(UIEdit.text, F.text, IsAnswer())
async def text_receive(message: Message, state: FSMContext, session: AsyncSession) -> None:
    key = (await state.get_data()).get("key")
    value = message.text.strip()
    if not 1 <= len(value) <= 32 or "\n" in value:
        await message.answer(f"{e('em_warn')} Matn 1–32 belgi va bitta qatorda bo'lishi kerak.")
        return
    await ui.set_text(key, value)
    await log_admin_action(session, message.from_user.id, "ui_text", f"{key}={value}")
    await state.clear()
    await message.answer(f"{e('em_ok')} Matn saqlandi!\n\n{editor_text(key)}", reply_markup=editor_kb(key))


# ---- standartga qaytarish
@router.callback_query(F.data.startswith("a:uir:"))
async def reset(cb: CallbackQuery) -> None:
    key = cb.data.split(":")[2]
    if key in SLOTS:
        await ui.reset(key)
    await cb.answer("♻️ Standart holatga qaytdi")
    await edit_or_send(cb, editor_text(key), editor_kb(key))


# ============================================================ guruhga rang berish
@router.callback_query(F.data.startswith("a:uigc:"))
async def group_color_pick(cb: CallbackQuery) -> None:
    group = cb.data.split(":")[2]
    if group not in GROUPS:
        await cb.answer()
        return
    await cb.answer()
    kb = ikb(
        [raw_ib("🔵 Ko'k", f"a:uigcs:{group}:primary", style="primary"),
         raw_ib("🟢 Yashil", f"a:uigcs:{group}:success", style="success")],
        [raw_ib("🔴 Qizil", f"a:uigcs:{group}:danger", style="danger"),
         raw_ib("⚪ Rangsiz", f"a:uigcs:{group}:default")],
        [ib("n_back", f"a:uig:{group}:0")],
    )
    await edit_or_send(cb, f"{e('em_palette')} <b>{GROUPS[group]}</b> guruhidagi <b>barcha</b> tugmalar uchun rang tanlang:", kb)


@router.callback_query(F.data.startswith("a:uigcs:"))
async def group_color_set(cb: CallbackQuery, session: AsyncSession) -> None:
    _, _, group, style = cb.data.split(":")
    if group not in GROUPS or style not in ("primary", "success", "danger", "default"):
        await cb.answer()
        return
    await ui.set_group_style(group, style)
    await log_admin_action(session, cb.from_user.id, "ui_group_color", f"{group}={style}")
    await cb.answer("🎨 Guruh rangi saqlandi")
    await edit_or_send(cb, f"{e('em_ok')} <b>{GROUPS[group]}</b> guruhi rangi yangilandi.",
                       ikb([ib("n_back", f"a:uig:{group}:0")]))


# ============================================================ ketma-ket (wizard) sozlash
def wizard_keys(scope: str) -> list[str]:
    if scope == "all":
        return [s.key for s in SLOT_LIST]
    return [s.key for s in group_slots(scope)]


@router.callback_query(F.data == "a:uiw")
async def wizard_scope(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    rows = [[ib("x_wizard", "a:uiw:all", text="Hammasi (ketma-ket)")]]
    rows += [[raw_ib(title, f"a:uiw:{g}", style="primary")] for g, title in GROUPS.items()]
    rows.append([ib("n_back", "a:set")])
    await edit_or_send(
        cb, f"{e('em_gem')} <b>Premium emoji sozlash</b>\n\nQaysi guruhni sozlaymiz? Bot ketma-ket har bir tugmani "
            f"ko'rsatadi, siz unga mos premium emoji yuborasiz.", ikb(*rows))


async def wizard_prompt(bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    keys, idx = data["keys"], data["idx"]
    key = keys[idx]
    upcoming = "\n".join(f"{n}. {SLOTS[k].emoji} {esc(ui.el(k).label)}" for n, k in enumerate(keys[idx:idx + 6], 1))
    text = (f"{e('em_gem')} <b>Premium emoji</b> — {idx + 1}/{len(keys)}\n\n"
            f"Hozir: <b>{SLOTS[key].emoji} {esc(ui.el(key).label)}</b>\n\n"
            f"Shu uchun premium emoji yuboring. Bir xabarda <b>bir nechta</b> premium emoji yuborsangiz, "
            f"ular quyidagi tartibda ketma-ket biriktiriladi:\n\n{upcoming}")
    kb = ikb([ib("n_next", "a:uiws", text="O'tkazib yuborish")], [ib("f_cancel", "a:uiwx", text="To'xtatish")])
    await bot.send_message(chat_id, text, reply_markup=kb)


@router.callback_query(F.data.startswith("a:uiw:"))
async def wizard_start(cb: CallbackQuery, state: FSMContext) -> None:
    scope = cb.data.split(":")[2]
    if scope != "all" and scope not in GROUPS:
        await cb.answer()
        return
    keys = wizard_keys(scope)
    await cb.answer()
    await state.set_state(UIEdit.wizard)
    await state.update_data(keys=keys, idx=0)
    await wizard_prompt(cb.bot, cb.from_user.id, state)


@router.message(UIEdit.wizard, IsAnswer())
async def wizard_input(message: Message, state: FSMContext, session: AsyncSession) -> None:
    found = extract_custom_emojis(message)
    if not found:
        await message.answer(f"{e('em_warn')} Premium emoji topilmadi. Premium emoji yuboring yoki "
                             f"«O'tkazib yuborish»ni bosing.")
        return
    data = await state.get_data()
    keys, idx = data["keys"], data["idx"]
    done = 0
    for emoji_id, char in found:
        if idx >= len(keys):
            break
        await ui.set_emoji(keys[idx], emoji_id, char)
        idx += 1
        done += 1
    await log_admin_action(session, message.from_user.id, "ui_wizard", f"{done} ta")
    await _wizard_next(message, state, keys, idx, f"{e('em_ok')} {done} ta premium emoji belgilandi.")


async def _wizard_next(message: Message, state: FSMContext, keys: list[str], idx: int, note: str) -> None:
    if idx >= len(keys):
        await state.clear()
        await message.answer(f"{note}\n\n🎉 <b>Sozlash yakunlandi!</b> Endi bot tugmalari va xabarlari premium emoji bilan chiqadi.",
                             reply_markup=ikb([ib("n_back", "a:set")]))
        return
    await state.update_data(idx=idx)
    await message.answer(note)
    await wizard_prompt(message.bot, message.chat.id, state)


@router.callback_query(F.data == "a:uiws")
async def wizard_skip(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if "keys" not in data:
        await cb.answer("Sozlash tugagan", show_alert=True)
        return
    await cb.answer()
    await _wizard_next(cb.message, state, data["keys"], data["idx"] + 1, "⏭ O'tkazib yuborildi.")


@router.callback_query(F.data == "a:uiwx")
async def wizard_stop(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer("To'xtatildi")
    await cb.message.answer(f"{e('em_info')} Sozlash to'xtatildi. Belgilanganlari saqlandi.",
                            reply_markup=ikb([ib("n_back", "a:set")]))
