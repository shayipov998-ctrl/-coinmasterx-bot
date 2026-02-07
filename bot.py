import os
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 5373171681  # <-- BU YERGA O'ZINGNI TELEGRAM IDINGNI YOZ

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")
conn.commit()


def add_user(user_id, referred_by=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, balance, referred_by) VALUES (?, ?, ?)",
            (user_id, 0, referred_by),
        )
        conn.commit()

        if referred_by:
            cursor.execute(
                "UPDATE users SET balance = balance + 10 WHERE user_id=?",
                (referred_by,),
            )
            conn.commit()


def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0


# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    referred_by = None
    if context.args:
        try:
            referred_by = int(context.args[0])
        except:
            pass

    add_user(user_id, referred_by)

    text = f"""
🚀 CoinMasterX Bot

💰 Balance: {get_balance(user_id)} coins

🔗 Referral link:
https://t.me/{context.bot.username}?start={user_id}
"""
    await update.message.reply_text(text)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 Sizning balansingiz: {bal} coins")


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]

    await update.message.reply_text(
        f"👑 Admin Panel\n\n👥 Users: {users_count}"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Xabar yozing.")
        return

    message = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            await context.bot.send_message(user[0], message)
        except:
            pass

    await update.message.reply_text("✅ Yuborildi.")


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
