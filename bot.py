import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Railway environment variable dan token olish
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("CoinMasterX bot ishga tushdi 🚀")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yordam uchun /start bosing")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
