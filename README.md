# 🤖 Xolboyev Dev — Telegram CRM-bot

Mijozlarni ro'yxatdan o'tkazadi, **bot yaratish arizalarini** qabul qiladi, adminga yetkazadi va ariza holatini
kuzatish imkonini beradi. Python 3.11+ · aiogram 3.25+ · SQLAlchemy 2 (SQLite / PostgreSQL).

## ✨ Imkoniyatlar

**Mijoz:** ro'yxatdan o'tish (ism, familiya, telefon, joylashuv — maxsus tugmalar bilan) · 8 qadamli ariza
(matn/rasm/video/hujjat, orqaga, tahrirlash, bekor qilish) · Arizalarim (sahifalab) · Ariza holati · Profil ·
Aloqa (adminga ariza ID bilan yozish) · Bot haqida.

**Admin (`🎛 Boshqaruv` tugmasi yoki `/admin`):** yangi/barcha arizalar · holatni o'zgartirish (mijozga avtomatik xabar) ·
mijozga yozish · foydalanuvchilar (bloklash) · statistika · ommaviy xabar · CSV eksport ·
**Sozlamalar:** 🎨 tugma dizayni · 💎 premium emoji · 🔒 majburiy obuna · 📝 bot matnlari.

## 💎 Premium emoji va tugma ranglari

`Boshqaruv → Sozlamalar` ichida har bir tugma uchun rang (🔵/🟢/🔴/⚪), matn va premium emoji belgilanadi.
**Premium emoji ID'lari kodda yo'q** — admin premium emoji yuboradi, bot ID'ni o'zi ajratib oladi.
`Premium emoji sozlash` bir xabarda ko'p emoji yuborishni qo'llaydi (ketma-ket tugmalarga biriktiriladi).

Shartlar (Telegram talabi): tugma va xabarlardagi premium emoji faqat **bot egasi** (BotFather'da botni yaratgan akkaunt)
Telegram Premium'ga ega bo'lsa ishlaydi. Muammo bo'lsa admin chatida `/premium_off`, `/colors_off` (qayta yoqish: `/premium_on`, `/colors_on`).

## 🔐 GitHub Secrets (token va admin ID)

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Qiymat |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` bergan token |
| `ADMIN_IDS` | Admin ID ([@userinfobot](https://t.me/userinfobot)); bir nechta bo'lsa vergul bilan: `111,222` |
| `DATABASE_URL` | PostgreSQL manzili (pastga qarang) |

Token va ID kodga yoki repoga **yozilmaydi** (`.env` `.gitignore`da).

## 🗄 Baza (majburiy): bepul PostgreSQL

GitHub Actions'da fayl tizimi har ishga tushganda tozalanadi, shuning uchun SQLite ishlamaydi.
[neon.tech](https://neon.tech) (yoki Supabase) da bepul baza yarating va **Connection string**ni (`postgresql://…`)
`DATABASE_URL` secret'iga qo'ying. Jadvallar birinchi ishga tushishda avtomatik yaratiladi.
(Supabase'da *pooler* emas, *direct* ulanishni oling.)

## 🚀 GitHub Actions orqali ishga tushirish

```bash
git init && git add . && git commit -m "Xolboyev Dev bot"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

1. Yuqoridagi 3 ta Secret'ni kiriting.
2. **Actions → Bot → Run workflow** (yoki `main`ga push qiling) — bot ishga tushadi.
3. `.github/workflows/bot.yml` har 5 soatda (cron) navbatga yangi job qo'yadi; eski job ~5 soat 50 daqiqada
   tugagach, yangisi uzilishsiz davom etadi. Uzilish payti yuborilgan xabarlarni Telegram 24 soat saqlaydi — bot qaytgach ularni qabul qiladi.

⚠️ **Bilib qo'ying:**
- Repo **ochiq (public)** bo'lsa Actions daqiqalari cheksiz; yopiq repoda bepul limit (oyiga 2000 daqiqa) bir necha kunda tugaydi.
- Ochiq repoda **loglar ham ochiq** — shuning uchun `LOG_LEVEL=WARNING`. Mijozlar ma'lumoti faqat bazada, repoda emas.
- GitHub Actions doimiy hosting uchun mo'ljallanmagan; foydalanish shartlari bilan tanishing. Bot istalgan hostingda
  (`python bot.py`) o'zgarishsiz ishlayveradi.
- Jarayondagi (tugallanmagan) ariza formalari xotirada turadi — qayta ishga tushishda foydalanuvchi qaytadan boshlaydi. Yuborilgan arizalar bazada xavfsiz.
- 60 kun repoda faollik bo'lmasa GitHub cron'ni o'chirib qo'yishi mumkin — **Run workflow** bosing.

## 💻 Lokal ishga tushirish

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # BOT_TOKEN va ADMIN_IDS ni yozing
python bot.py
```

## 🗂 Tuzilma

```
bot.py · config.py · requirements.txt · .env.example · .gitignore · Procfile
database/     models.py, database.py
handlers/     start, registration, orders, profile, contact, admin, admin_comm, admin_settings, admin_ui, common
keyboards/    builder (rang + premium emoji), user, admin
services/     ui, order_service, notifications, subscription, settings_service
middlewares/  db_session, access (blok + majburiy obuna)
utils/        registry (barcha tugma/emoji slotlari), texts, filters, helpers, steps, constants, logger
states/       states.py
.github/workflows/  bot.yml (botni ishga tushirish + cron), ci.yml (tekshiruv)
```

## 🔒 Majburiy obuna

`Sozlamalar → Majburiy obuna → Kanal qo'shish`. Avval botni kanalga **admin** qiling; kanalni `@username`, `t.me/…`,
ID yoki forward qilingan xabar orqali qo'shing, so'ng obunani yoqing (adminlar tekshirilmaydi).

## 🛡 Xavfsizlik

Maxfiy qiymatlar faqat Secrets'da · admin faqat `ADMIN_IDS` bo'yicha · SQLAlchemy parametrli so'rovlari ·
matnlar HTML-escape · kiritishlar validatsiya · xatolar `logs/bot.log` ga · telefon/joylashuv faqat buyurtma uchun.
