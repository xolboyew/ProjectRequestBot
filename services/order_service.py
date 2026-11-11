"""Foydalanuvchi, ariza va statistika bilan ishlash (biznes logika)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (AdminAction, Message, Order, OrderFile, OrderHistory, User, utcnow)
from utils.constants import PAGE_SIZE, PENDING, STATUSES, TZ

ORDER_FIELDS = (
    "bot_type", "bot_name", "bot_username", "purpose",
    "features", "admin_panel", "extra_requirements", "extra_info",
)


# ------------------------------------------------------------------ foydalanuvchi
async def get_or_create_user(session: AsyncSession, tg: TgUser) -> User:
    user = await session.scalar(select(User).where(User.tg_id == tg.id))
    now = utcnow()
    if user is None:
        user = User(tg_id=tg.id, username=tg.username, tg_full_name=tg.full_name, last_seen=now)
        session.add(user)
        try:
            await session.flush()
        except IntegrityError:  # ikki xabar bir vaqtda kelganda — boshqa jarayon allaqachon yaratgan
            await session.rollback()
            return await session.scalar(select(User).where(User.tg_id == tg.id))
        return user
    changed = False
    if user.username != tg.username:
        user.username, changed = tg.username, True
    if user.tg_full_name != tg.full_name:
        user.tg_full_name, changed = tg.full_name, True
    if changed or (now - user.last_seen) > timedelta(minutes=5):
        user.last_seen = now
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def list_users(session: AsyncSession, page: int, size: int = PAGE_SIZE + 3):
    total = await session.scalar(select(func.count(User.id)))
    rows = (
        await session.scalars(select(User).order_by(User.id.desc()).offset(page * size).limit(size))
    ).all()
    return rows, total or 0, size


async def user_orders_count(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(select(func.count(Order.id)).where(Order.user_id == user_id)) or 0


async def all_user_tg_ids(session: AsyncSession) -> list[int]:
    rows = await session.scalars(select(User.tg_id).where(User.is_banned.is_(False)))
    return list(rows.all())


# ------------------------------------------------------------------ ariza
async def create_order(session: AsyncSession, user: User, answers: dict, files: list[dict]) -> Order:
    order = Order(user_id=user.id, status=PENDING, **{f: (answers.get(f) or None) for f in ORDER_FIELDS})
    session.add(order)
    await session.flush()
    for f in files:
        session.add(OrderFile(order_id=order.id, file_id=f["file_id"], file_type=f["type"], caption=f.get("caption")))
    session.add(OrderHistory(order_id=order.id, old_status=None, new_status=PENDING,
                             changed_by=user.tg_id, note="Ariza yaratildi"))
    await session.commit()
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.get(Order, order_id)


async def order_files(session: AsyncSession, order_id: int) -> list[OrderFile]:
    return list((await session.scalars(select(OrderFile).where(OrderFile.order_id == order_id))).all())


async def order_history(session: AsyncSession, order_id: int) -> list[OrderHistory]:
    q = select(OrderHistory).where(OrderHistory.order_id == order_id).order_by(OrderHistory.id)
    return list((await session.scalars(q)).all())


async def list_orders(session: AsyncSession, *, status: str | None = None, user_id: int | None = None,
                      page: int = 0, size: int = PAGE_SIZE):
    q, cq = select(Order), select(func.count(Order.id))
    if status:
        q, cq = q.where(Order.status == status), cq.where(Order.status == status)
    if user_id:
        q, cq = q.where(Order.user_id == user_id), cq.where(Order.user_id == user_id)
    total = await session.scalar(cq) or 0
    rows = (await session.scalars(q.order_by(Order.id.desc()).offset(page * size).limit(size))).all()
    return list(rows), total


async def user_active_orders(session: AsyncSession, user_id: int, limit: int = 8) -> list[Order]:
    q = (select(Order).where(Order.user_id == user_id, Order.status.in_(("pending", "accepted", "in_progress")))
         .order_by(Order.id.desc()).limit(limit))
    return list((await session.scalars(q)).all())


async def user_status_counts(session: AsyncSession, user_id: int) -> dict[str, int]:
    rows = await session.execute(
        select(Order.status, func.count(Order.id)).where(Order.user_id == user_id).group_by(Order.status))
    counts = {s: 0 for s in STATUSES}
    counts.update({st: n for st, n in rows.all()})
    return counts


async def change_status(session: AsyncSession, order: Order, new_status: str, admin_tg_id: int,
                        note: str | None = None) -> str:
    old = order.status
    order.status = new_status
    order.updated_at = utcnow()
    session.add(OrderHistory(order_id=order.id, old_status=old, new_status=new_status,
                             changed_by=admin_tg_id, note=note))
    await log_admin_action(session, admin_tg_id, "status_change", f"#{order.id}: {old} -> {new_status}")
    await session.commit()
    return old


# ------------------------------------------------------------------ admin harakatlari, xabarlar
async def log_admin_action(session: AsyncSession, admin_tg_id: int, action: str, details: str = "") -> None:
    session.add(AdminAction(admin_tg_id=admin_tg_id, action=action, details=details[:1000]))


async def save_message(session: AsyncSession, *, user_id: int, order_id: int | None, direction: str,
                       sender_tg_id: int, text: str | None) -> None:
    session.add(Message(user_id=user_id, order_id=order_id or None, direction=direction,
                        sender_tg_id=sender_tg_id, text=(text or "")[:4000]))


# ------------------------------------------------------------------ statistika
async def get_stats(session: AsyncSession) -> dict:
    now = utcnow()
    local_midnight = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    today = local_midnight.astimezone(timezone.utc).replace(tzinfo=None)
    week = now - timedelta(days=7)

    async def count(model_col, *conds) -> int:
        return await session.scalar(select(func.count(model_col)).where(*conds)) or 0

    stats = {
        "users": await count(User.id),
        "registered": await count(User.id, User.is_registered.is_(True)),
        "banned": await count(User.id, User.is_banned.is_(True)),
        "users_today": await count(User.id, User.created_at >= today),
        "orders": await count(Order.id),
        "orders_today": await count(Order.id, Order.created_at >= today),
        "orders_week": await count(Order.id, Order.created_at >= week),
        "by_status": {s: 0 for s in STATUSES},
    }
    rows = await session.execute(select(Order.status, func.count(Order.id)).group_by(Order.status))
    stats["by_status"].update({st: n for st, n in rows.all()})
    return stats


async def export_rows(session: AsyncSession) -> list[Order]:
    return list((await session.scalars(select(Order).order_by(Order.id))).all())
