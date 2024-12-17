from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
import telegram
import logging
import os
from pathlib import Path
import random
import time
from typing import Dict, List
from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from telegram.ext import JobQueue

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
# BOT_TOKEN = "7599009031:AAHlE1-9sMGzmbEboe4ONQZENrNcPLrrYNw"
BOT_TOKEN = "8063156470:AAG0MIHhjA4L_vKqtPr_kKeiPdxG6zTNgHQ"
MONGODB_URI = "mongodb+srv://kelvin-1013:everysecond1013@cluster0.z54oc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
last_message_time = 0
MESSAGE_COOLDOWN = 100  # seconds
STATS_INTERVAL = 300  # 5 minutes in seconds

# MongoDB connection
def get_database() -> Database:
    """Get MongoDB database connection"""
    try:
        client = MongoClient(MONGODB_URI)
        return client.presale
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def fetch_presale_stats() -> dict:
    """Fetch current presale statistics from MongoDB"""
    try:
        db = get_database()
        current_presale = db.current_presale.find_one({})
        
        if current_presale and 'presaleInfo' in current_presale:
            return current_presale['presaleInfo']
        
        return None
    except Exception as e:
        logger.error(f"Error fetching presale stats from MongoDB: {str(e)}")
        return None

async def get_total_buyers() -> int:
    """Get total number of unique buyers"""
    try:
        db = get_database()
        return db.buys.count_documents({})
    except Exception as e:
        logger.error(f"Error fetching buyer count: {str(e)}")
        return 0

async def send_stats_update(context: ContextTypes.DEFAULT_TYPE):
    """Send periodic statistics update to the group"""
    try:
        stats = await fetch_presale_stats()
        total_buyers = await get_total_buyers()
        
        if not stats:
            logger.error("Failed to fetch presale statistics")
            return

        # Format the statistics message
        message = (
            "🚀 *Presale Statistics Update* 🚀\n\n"
            f"💰 Total Buyers: {total_buyers}\n"
            f"💰 Tokens Sold: {stats.get('soldTokenAmount', 0):,.2f}\n"
            f"💎 Total SOL Received: {stats.get('receivedSolAmount', 0):,.2f} SOL\n"
            f"📊 Progress: {(stats.get('soldTokenAmount', 0) / stats.get('hardcapAmount', 1) * 100):,.1f}%\n\n"
            f"🎯 Hardcap: {stats.get('hardcapAmount', 0):,.2f}\n"
            f"💫 Price per Token: {stats.get('pricePerToken', 0):,.6f} SOL\n"
            f"\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        # Send to all groups the bot is in
        for chat_id in context.bot_data.get('group_chats', set()):
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except telegram.error.TelegramError as e:
                logger.error(f"Failed to send stats to group {chat_id}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in send_stats_update: {str(e)}")

def load_welcome_messages() -> List[str]:
    """Load welcome messages from files"""
    messages = []
    try:
        # Load all messages from message1.txt to message3.txt
        for i in range(1, 4):
            message_path = Path(f'./data/message{i}.txt')
            if message_path.exists():
                with open(message_path, 'r', encoding='utf-8') as f:
                    messages.append(f.read().strip())
        
        if not messages:
            logger.error("No welcome message files found")
            messages.append("Welcome to our group!")  # Fallback message
            
        return messages
    except Exception as e:
        logger.error("Error loading welcome messages: %s", str(e))
        return ["Welcome to our group!"]  # Fallback message

def get_random_banner() -> Path:
    """Get a random banner image from available options"""
    banner_files = [
        'tmonk-banner1.jpg',
        'tmonk-banner2.jpg',
        'tmonk-banner3.jpg'
    ]
    
    available_banners = []
    for banner in banner_files:
        banner_path = Path(f'./data/{banner}')
        if banner_path.exists():
            available_banners.append(banner_path)
    
    return random.choice(available_banners) if available_banners else None

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members when they join the group"""
    global last_message_time
    
    try:
        current_time = time.time()
        
        # Check cooldown
        if current_time - last_message_time < MESSAGE_COOLDOWN:
            logger.info("Skipping welcome message due to cooldown")
            return
        
        for new_member in update.message.new_chat_members:
            # Don't welcome the bot itself
            if new_member.id != context.bot.id:
                # Get username or full name
                username = new_member.username or f"{new_member.first_name} {new_member.last_name or ''}"
                
                # Load and select random message
                messages = load_welcome_messages()
                welcome_message = random.choice(messages)
                
                # Add personalized greeting
                welcome_message = f"Hi {username}!\n\n{welcome_message}"
                
                try:
                    # Get presale stats
                    stats = await fetch_presale_stats()
                    total_buyers = await get_total_buyers()
                    
                    if stats:
                        stats_message = (
                            "\n\n🚀 *Current Presale Status* 🚀\n\n"
                            f"💰 Total Buyers: {total_buyers}\n"
                            f"💰 Tokens Sold: {stats.get('soldTokenAmount', 0):,.2f}\n"
                            f"💎 Total SOL Received: {stats.get('receivedSolAmount', 0):,.2f} SOL\n"
                            f"📊 Progress: {(stats.get('soldTokenAmount', 0) / stats.get('hardcapAmount', 1) * 100):,.1f}%\n\n"
                            f"🎯 Hardcap: {stats.get('hardcapAmount', 0):,.2f}\n"
                            f"💫 Price per Token: {stats.get('pricePerToken', 0):,.6f} SOL"
                        )
                        welcome_message += stats_message
                    
                    # Get random banner
                    banner_path = get_random_banner()
                    if banner_path:
                        await update.message.reply_photo(
                            photo=open(banner_path, 'rb'),
                            caption=welcome_message,
                            parse_mode='Markdown'
                        )
                    else:
                        # Send text-only message if no banner
                        await update.message.reply_text(
                            welcome_message,
                            parse_mode='Markdown'
                        )
                    
                    # Update last message time
                    last_message_time = current_time
                    
                except telegram.error.TelegramError as e:
                    logger.error("Failed to send welcome message: %s", str(e))
                    
    except Exception as e:
        logger.error("Error in welcome_new_member: %s", str(e))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    try:
        await update.message.reply_text("Bot is running! Add me to a group to welcome new members.")
    except telegram.error.TelegramError as e:
        logger.error("Failed to send start message: %s", str(e))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error("Update '%s' caused error '%s'", update, context.error)
    try:
        raise context.error
    except telegram.error.NetworkError:
        logger.error("Network error occurred")
    except telegram.error.TimedOut:
        logger.error("Request timed out")
    except telegram.error.BadRequest as e:
        logger.error("Bad request: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))

async def track_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track which chats the bot is in"""
    if not hasattr(context.bot_data, 'group_chats'):
        context.bot_data['group_chats'] = set()
    
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup']:
        context.bot_data['group_chats'].add(chat_id)

def main():
    """Start the bot"""
    try:
        # Create application with retry settings
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .connect_timeout(30.0)
            .read_timeout(30.0)
            .build()
        )

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(MessageHandler(filters.ALL, track_chat))  # Track all chats
        application.add_error_handler(error_handler)

        # Add job for periodic stats updates
        application.job_queue.run_repeating(
            send_stats_update,
            interval=STATS_INTERVAL,
            first=10,
            name='periodic_stats'
        )
        logger.info("Successfully set up periodic stats updates")

        # Ensure data directory exists
        os.makedirs('./data', exist_ok=True)

        # Start the bot
        logger.info("Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except telegram.error.InvalidToken:
        logger.error("Invalid bot token")
    except Exception as e:
        logger.error("Fatal error: %s", str(e))

if __name__ == "__main__":
    main() 