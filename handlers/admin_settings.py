"""Admin sozlamalari: menyu, bot matnlari va majburiy obuna."""
from __future__ import annotations

import html
import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Channel
from keyboards.admin import cancel_inline, settings_kb
from keyboards.builder import ib, ikb, raw_ib
from services.settings_service import app_settings
from services.ui import ui
from services.order_service import log_admin_action
from states.states import SubAdd, TextEdit
from utils.filters import IsAdmin, IsAnswer
from utils.helpers import edit_or_send
from utils.texts import e, render

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

TEXT_ITEMS = {
    "welcome_text": "Salomlashish matni",
    "about_text": "«Bot haqida» matni",
    "contact_text": "«Aloqa» matni",
    "contact_username": "Aloqa uchun admin username",
}


# ============================================================ sozlamalar menyusi
def settings_text() -> str:
    return (f"{e('em_gear')} <b>Sozlamalar</b>\n\n"
            f"{e('em_palette')} Tugmalar rangi, matni va premium emojilarini o'zgartiring.\n"
            f"{e('em_lock')} Majburiy obuna kanallarini boshqaring.\n"
            f"{e('em_edit')} Bot matnlarini tahrirlang.")


@router.callback_query(F.data == "a:set")
async def settings_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await edit_or_send(cb, settings_text(), settings_kb(ui.premium_on, ui.colors_on))


@router.callback_query(F.data.startswith("a:tg:"))
async def toggle(cb: CallbackQuery) -> None:
    key = "premium_on" if cb.data.endswith("premium") else "colors_on"
    await app_settings.set(key, "0" if app_settings.get_bool(key) else "1")
    await cb.answer("Saqlandi")
    await edit_or_send(cb, settings_text(), settings_kb(ui.premium_on, ui.colors_on))


# ============================================================ matnlar
@router.callback_query(F.data == "a:tx")
async def texts_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    rows = [[raw_ib(title, f"a:txe:{name}", style="primary")] for name, title in TEXT_ITEMS.items()]
    rows.append([ib("n_back", "a:set")])
    await edit_or_send(cb, f"{e('em_edit')} <b>Bot matnlari</b>\n\nQaysi matnni o'zgartirasiz?", ikb(*rows))


@router.callback_query(F.data.startswith("a:txe:"))
async def text_edit_start(cb: CallbackQuery, state: FSMContext) -> None:
    name = cb.data.split(":")[2]
    if name not in TEXT_ITEMS:
        await cb.answer()
        return
    await cb.answer()
    await state.set_state(TextEdit.value)
    await state.update_data(name=name)
    current = html.escape(app_settings.get(name)) or "(bo'sh)"
    hint = ""
    if name != "contact_username":
        hint = ("\n\n<i>Maslahat: matnga premium emoji'ni to'g'ridan-to'g'ri qo'shishingiz mumkin. "
                "<code>{name}</code> — mijoz ismi, <code>{em_star}</code>, <code>{em_rocket}</code> kabi belgilar "
                "tugma sozlamalaridagi premium emojiga almashadi.</i>")
    kb = ikb([ib("x_reset", f"a:txr:{name}")], [ib("f_cancel", "a:tx", text="Bekor qilish")])
    await cb.message.answer(f"{e('em_edit')} <b>{TEXT_ITEMS[name]}</b>\n\nHozirgi qiymat:\n<pre>{current}</pre>\n"
                            f"Yangi qiymatni yuboring{hint}", reply_markup=kb)


@router.callback_query(F.data.startswith("a:txr:"))
async def text_reset(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    name = cb.data.split(":")[2]
    if name in TEXT_ITEMS:
        await app_settings.reset(name)
        await log_admin_action(session, cb.from_user.id, "text_reset", name)
    await state.clear()
    await cb.answer("♻️ Standart holatga qaytarildi")
    await edit_or_send(cb, f"{e('em_ok')} <b>{TEXT_ITEMS.get(name, name)}</b> standart holatga qaytarildi.",
                       ikb([ib("n_back", "a:tx")]))


@router.message(TextEdit.value, F.text, IsAnswer())
async def text_edit_save(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = (await state.get_data())["name"]
    if name == "contact_username":
        value = message.text.strip()
        if value in ("-", "0"):
            value = ""
        elif not re.fullmatch(r"@?[A-Za-z0-9_]{4,32}", value):
            await message.answer(f"{e('em_warn')} Username noto'g'ri. Masalan: <code>@xolboyev</code> "
                                 f"(o'chirish uchun <code>-</code> yuboring).")
            return
        value = value.lstrip("@")
    else:
        value = message.html_text
        if len(value) > 3500:
            await message.answer(f"{e('em_warn')} Matn juda uzun.")
            return
    await app_settings.set(name, value)
    await log_admin_action(session, message.from_user.id, "text_edit", name)
    await state.clear()
    preview = render(value, name="Azizbek") if name != "contact_username" else f"@{value}" if value else "(bo'sh)"
    await message.answer(f"{e('em_ok')} Saqlandi. Ko'rinishi:\n\n{preview}",
                         reply_markup=ikb([ib("n_back", "a:tx")]))


# ============================================================ majburiy obuna
async def sub_view(session: AsyncSession):
    channels = list((await session.scalars(select(Channel).order_by(Channel.id))).all())
    enabled = app_settings.get_bool("sub_enabled")
    lines = [f"{e('em_lock')} <b>Majburiy obuna</b>\n",
             f"Holati: {'✅ <b>yoqilgan</b>' if enabled else '❌ <b>o‘chirilgan</b>'}\n"]
    if channels:
        lines.append("<b>Kanallar:</b>")
        lines += [f"{i}. {html.escape(c.title)}" for i, c in enumerate(channels, 1)]
    else:
        lines.append("Kanallar qo'shilmagan.")
    lines.append("\n<i>Bot kanalda admin bo'lishi shart. Obuna yoqilganda barcha foydalanuvchilar "
                 "(adminlardan tashqari) kanallarga a'zo bo'lishi kerak.</i>")
    rows = [[ib("t_toggle", "a:sbt", text="Obuna: yoqilgan" if enabled else "Obuna: o'chirilgan",
                style="success" if enabled else "danger")],
            [ib("sb_add", "a:sba")]]
    rows += [[ib("sb_del", f"a:sbd:{c.id}", text=f"O'chirish: {c.title[:24]}")] for c in channels]
    rows.append([ib("n_back", "a:set")])
    return "\n".join(lines), ikb(*rows)


@router.callback_query(F.data == "a:sub")
async def sub_menu(cb: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await cb.answer()
    text, kb = await sub_view(session)
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data == "a:sbt")
async def sub_toggle(cb: CallbackQuery, session: AsyncSession) -> None:
    new = "0" if app_settings.get_bool("sub_enabled") else "1"
    if new == "1" and not (await session.scalars(select(Channel).where(Channel.is_active.is_(True)))).first():
        await cb.answer("Avval kamida bitta kanal qo'shing", show_alert=True)
        return
    await app_settings.set("sub_enabled", new)
    await log_admin_action(session, cb.from_user.id, "sub_toggle", new)
    await cb.answer("Saqlandi")
    text, kb = await sub_view(session)
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data.startswith("a:sbd:"))
async def sub_delete(cb: CallbackQuery, session: AsyncSession) -> None:
    ch = await session.get(Channel, int(cb.data.split(":")[2]))
    if ch:
        await session.delete(ch)
        await session.flush()
        await log_admin_action(session, cb.from_user.id, "sub_delete", ch.title)
    left = (await session.scalars(select(Channel).where(Channel.is_active.is_(True)))).first()
    if not left and app_settings.get_bool("sub_enabled"):
        await app_settings.set("sub_enabled", "0")
    await cb.answer("🗑 O'chirildi")
    text, kb = await sub_view(session)
    await edit_or_send(cb, text, kb)


@router.callback_query(F.data == "a:sba")
async def sub_add_start(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await state.set_state(SubAdd.channel)
    await cb.message.answer(
        f"{e('em_link')} <b>Kanal qo'shish</b>\n\nBotni avval kanalga <b>admin</b> qiling, so'ng quyidagilardan birini yuboring:\n"
        f"• kanal username'i: <code>@kanal_nomi</code>\n• <code>t.me/kanal_nomi</code> havolasi\n"
        f"• kanal ID'si (<code>-100…</code>)\n• kanaldan <b>forward</b> qilingan xabar (yopiq kanallar uchun)",
        reply_markup=cancel_inline("a:sub"))


async def resolve_chat(bot, message: Message):
    origin = message.forward_origin
    if origin is not None and getattr(origin, "type", None) == "channel":
        return await bot.get_chat(origin.chat.id)
    text = (message.text or "").strip()
    if not text:
        raise ValueError("Matn, username yoki forward qilingan xabar yuboring.")
    m = re.match(r"^(?:https?://)?t\.me/([A-Za-z0-9_]{4,32})/?", text)
    if m:
        text = "@" + m.group(1)
    if "+" in text or "joinchat" in text:
        raise ValueError("Yopiq havoladan foydalanib bo'lmaydi. Kanaldan biror xabarni forward qiling yoki ID yuboring.")
    ident = int(text) if re.fullmatch(r"-?\d{5,}", text) else (text if text.startswith("@") else "@" + text)
    return await bot.get_chat(ident)


@router.message(SubAdd.channel, IsAnswer())
async def sub_add_receive(message: Message, state: FSMContext, session: AsyncSession) -> None:
    bot = message.bot
    try:
        chat = await resolve_chat(bot, message)
        if chat.type not in ("channel", "supergroup", "group"):
            raise ValueError("Bu kanal yoki guruh emas.")
        me = await bot.me()
        member = await bot.get_chat_member(chat.id, me.id)
        if getattr(member.status, "value", member.status) not in ("administrator", "creator"):
            raise ValueError("Bot bu kanalda admin emas. Avval botni kanalga admin qiling.")
        if chat.username:
            url = f"https://t.me/{chat.username}"
        else:
            url = (await bot.create_chat_invite_link(chat.id)).invite_link
    except ValueError as ex:
        await message.answer(f"{e('em_warn')} {html.escape(str(ex))}")
        return
    except Exception as ex:
        logger.info("Kanal qo'shishda xato: %s", ex)
        await message.answer(f"{e('em_warn')} Kanalni topib bo'lmadi yoki bot unda admin emas. Tekshirib, qayta yuboring.")
        return
    if await session.scalar(select(Channel).where(Channel.chat_id == chat.id)):
        await message.answer(f"{e('em_info')} Bu kanal allaqachon qo'shilgan.")
        return
    session.add(Channel(chat_id=chat.id, title=chat.title or str(chat.id), url=url))
    await log_admin_action(session, message.from_user.id, "sub_add", chat.title or str(chat.id))
    await state.clear()
    await session.flush()
    text, kb = await sub_view(session)
    await message.answer(f"{e('em_ok')} Kanal qo'shildi: <b>{html.escape(chat.title or '')}</b>\n\n{text}", reply_markup=kb)
