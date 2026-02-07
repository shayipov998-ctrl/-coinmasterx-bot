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

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    last_bonus TEXT
)
""")
conn.commit()


def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0


def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()


def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


def get_last_bonus(user_id):
    cursor.execute("SELECT last_bonus FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def set_last_bonus(user_id, date):
    cursor.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (date, user_id))
    conn.commit()


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)

    keyboard = [
        [InlineKeyboardButton("💰 Balans", callback_data="balance")],
        [InlineKeyboardButton("🎁 Bonus (+10)", callback_data="bonus")],
    ]

    if user.id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("📊 Admin Panel", callback_data="admin")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"Salom {user.first_name} 👋\n\nBot to‘liq ishlayapti 🚀"

    await update.message.reply_text(text, reply_markup=reply_markup)


# ===== BUTTON HANDLER =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(f"💰 Sizning balansingiz: {balance} coin")

    elif query.data == "bonus":
        today = str(datetime.date.today())
        last_bonus = get_last_bonus(user_id)

        if last_bonus == today:
            await query.answer("❌ Siz bugun bonus olgansiz!", show_alert=True)
        else:
            update_balance(user_id, 10)
            set_last_bonus(user_id, today)
            await query.edit_message_text("🎉 Bonus qo‘shildi! +10 coin")

    elif query.data == "admin":
        if user_id == ADMIN_ID:
            users = get_users_count()
            await query.edit_message_text(
                f"📊 ADMIN PANEL\n\n👥 Foydalanuvchilar soni: {users}"
            )
        else:
            await query.answer("❌ Siz admin emassiz!", show_alert=True)


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Bot ishlayapti 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
