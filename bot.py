from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import telegram

# Replace with your bot token
BOT_TOKEN = "8063156470:AAG0MIHhjA4L_vKqtPr_kKeiPdxG6zTNgHQ"

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members when they join the group"""
    for new_member in update.message.new_chat_members:
        # Don't welcome the bot itself
        if new_member.id != context.bot.id:
            welcome_message = """🚨 Welcome to $TMONK community! 🐒💸

 Secure $TMONK, the eco-friendly meme coin backed by a gold reserve wallet for stability, supporting clean energy and real-world projects.

💸 Buy Now:
👉 https://app.tmonk.net/

🔗 Stay Connected:
🌐 https://tmonk.net
🐦 https://x.com/TMONK777
📸 https://instagram.com/tmonk777
💬 https://discord.com/invite/cpjsEXcKvU
🔊 https://t.me/+gcK4YOe5sXZjZWY5"""
            
            # Send image first
            await update.message.reply_photo(photo=open("./data/tmonk-banner.png", "rb"))
            # Then send the welcome message
            await update.message.reply_text(welcome_message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    await update.message.reply_text("Bot is running! Add me to a group to welcome new members.")

def main():
    """Start the bot"""
    # Create application with retry settings
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)  # Increase connection timeout
        .read_timeout(30.0)     # Increase read timeout
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Start the bot with error handling
    while True:
        try:
            print("Bot is running...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except telegram.error.TimedOut:
            print("Connection timed out. Retrying...")
            continue
        except Exception as e:
            print(f"Error occurred: {e}")
            break

if __name__ == "__main__":
    main() 