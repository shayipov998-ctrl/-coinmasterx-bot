import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================== CONFIG ==================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5373171681  # Sening ID
DB_NAME = "database.db"

# ================== DATABASE ==================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    joined_at TEXT
)
""")

conn.commit()

# ================== FUNCTIONS ==================

def add_user(user):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username, joined_at) VALUES (?, ?, ?)",
            (user.id, user.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
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

def get_total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)

    keyboard = [
        [InlineKeyboardButton("💰 Balans", callback_data="balance")],
        [InlineKeyboardButton("🎁 Bonus (+10)", callback_data="bonus")],
    ]

    if user.id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("📊 Admin Panel", callback_data="admin")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Salom {user.first_name} 👋\n\nBot to‘liq ishlayapti 🚀",
        reply_markup=reply_markup,
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(f"💰 Sizning balansingiz: {balance} coin")

    elif query.data == "bonus":
        update_balance(user_id, 10)
        balance = get_balance(user_id)
        await query.edit_message_text(
            f"🎉 10 coin qo‘shildi!\n\nYangi balans: {balance}"
        )

    elif query.data == "admin" and user_id == ADMIN_ID:
        total = get_total_users()
        await query.edit_message_text(
            f"📊 ADMIN PANEL\n\n👥 Foydalanuvchilar soni: {total}"
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        total = get_total_users()
        await update.message.reply_text(
            f"📊 Statistika:\n\n👥 Foydalanuvchilar: {total}"
        )

# ================== MAIN ==================

def main():
    if not TOKEN:
        print("TOKEN topilmadi!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishga tushdi 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
