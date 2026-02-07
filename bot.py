import os
import sqlite3
import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5373171681
CHANNEL_USERNAME = "@sss_sssa_1"

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    last_bonus TEXT,
    ref_by INTEGER,
    banned INTEGER DEFAULT 0
)
""")
conn.commit()


# ===== DATABASE FUNCTIONS =====

def add_user(user_id, ref_by=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, ref_by) VALUES (?, ?)",
            (user_id, ref_by),
        )
        conn.commit()


def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0


def update_balance(user_id, amount):
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()


def get_last_bonus(user_id):
    cursor.execute("SELECT last_bonus FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def set_last_bonus(user_id, date):
    cursor.execute(
        "UPDATE users SET last_bonus=? WHERE user_id=?",
        (date, user_id),
    )
    conn.commit()


def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users WHERE banned=0")
    return cursor.fetchone()[0]


def get_top_users():
    cursor.execute(
        "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 5"
    )
    return cursor.fetchall()


def get_all_users():
    cursor.execute("SELECT user_id FROM users WHERE banned=0")
    return [row[0] for row in cursor.fetchall()]


def ban_user(user_id):
    cursor.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
    conn.commit()


def is_banned(user_id):
    cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1


# ===== CHANNEL CHECK =====

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ===== MENU =====

def main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("💰 Balans", callback_data="balance")],
        [InlineKeyboardButton("🎁 Bonus", callback_data="bonus")],
        [InlineKeyboardButton("🏆 Top 5", callback_data="top")],
        [InlineKeyboardButton("👥 Referal", callback_data="ref")],
    ]

    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("📊 Admin Panel", callback_data="admin")]
        )

    return InlineKeyboardMarkup(keyboard)


# ===== START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_banned(user.id):
        return

    # Referral
    ref_by = None
    if context.args:
        try:
            ref_by = int(context.args[0])
            if ref_by == user.id:
                ref_by = None
        except:
            ref_by = None

    add_user(user.id, ref_by)

    # Referral bonus
    if ref_by:
        update_balance(ref_by, 20)
        update_balance(user.id, 10)

    # Subscription check
    subscribed = await check_subscription(user.id, context)
    if not subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "Botdan foydalanish uchun kanalga a'zo bo‘ling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = f"Salom {user.first_name} 👋\n\nBot PRO versiya ishlayapti 🚀"
    await update.message.reply_text(text, reply_markup=main_menu(user.id))


# ===== BUTTONS =====

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if is_banned(user_id):
        return

    if query.data == "check_sub":
        subscribed = await check_subscription(user_id, context)
        if subscribed:
            await query.edit_message_text(
                "Tasdiqlandi ✅",
                reply_markup=main_menu(user_id)
            )
        else:
            await query.answer("Hali a'zo emassiz!", show_alert=True)

    elif query.data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(
            f"💰 Balansingiz: {balance} coin",
            reply_markup=main_menu(user_id)
        )

    elif query.data == "bonus":
        today = str(datetime.date.today())
        last_bonus = get_last_bonus(user_id)

        if last_bonus == today:
            await query.answer("Bugungi bonus olingan!", show_alert=True)
        else:
            update_balance(user_id, 10)
            set_last_bonus(user_id, today)
            await query.edit_message_text(
                "🎉 +10 coin qo‘shildi!",
                reply_markup=main_menu(user_id)
            )

    elif query.data == "top":
        top = get_top_users()
        text = "🏆 TOP 5\n\n"
        for i, user in enumerate(top, 1):
            text += f"{i}. ID: {user[0]} — {user[1]} coin\n"

        await query.edit_message_text(text, reply_markup=main_menu(user_id))

    elif query.data == "ref":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 Sizning referal linkingiz:\n\n{link}\n\n"
            "Har taklif uchun +20 coin!",
            reply_markup=main_menu(user_id)
        )

    elif query.data == "admin" and user_id == ADMIN_ID:
        users = get_users_count()
        await query.edit_message_text(
            f"📊 ADMIN PANEL\n\n👥 Userlar: {users}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "back":
        await query.edit_message_text(
            "Asosiy menyu",
            reply_markup=main_menu(user_id)
        )


# ===== MAIN =====

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("PRO BOT ishlayapti 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
