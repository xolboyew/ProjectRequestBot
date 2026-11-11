from datetime import timedelta, timezone

TZ = timezone(timedelta(hours=5))  # Toshkent vaqti
PAGE_SIZE = 5

PENDING = "pending"
ACCEPTED = "accepted"
IN_PROGRESS = "in_progress"
DONE = "done"
REJECTED = "rejected"

STATUSES = (PENDING, ACCEPTED, IN_PROGRESS, DONE, REJECTED)
STATUS_TITLE = {
    PENDING: "Kutilmoqda",
    ACCEPTED: "Qabul qilindi",
    IN_PROGRESS: "Jarayonda",
    DONE: "Yakunlandi",
    REJECTED: "Rad etildi",
}
STATUS_SLOT = {s: f"st_{s}" for s in STATUSES}
STATUS_ACTION_SLOT = {
    ACCEPTED: "s_accept",
    IN_PROGRESS: "s_progress",
    DONE: "s_done",
    REJECTED: "s_reject",
}
ACTIVE_STATUSES = (PENDING, ACCEPTED, IN_PROGRESS)
