import logging
from telegram.ext import ApplicationBuilder, Application
from config import TOKEN, COMMANDS
from database import Database
from workout_manager import WorkoutManager
from reminder import ReminderManager
from handlers import BotHandlers

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def setup_commands(application: Application) -> None:
    """Set up bot commands."""
    await application.bot.set_my_commands([
        (command, description) for command, description in COMMANDS.items()
    ])

def main():
    """Initialize and start the bot"""
    if not TOKEN:
        print("Error: Telegram Bot Token not found. Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return

    try:
        # Initialize components
        database = Database()
        workout_manager = WorkoutManager()

        # Create application with specific settings to avoid conflicts
        application = (
            ApplicationBuilder()
            .token(TOKEN)
            .concurrent_updates(False)    # Disable concurrent updates
            .build()
        )

        # Initialize reminder manager with bot instance
        reminder_manager = ReminderManager(application.bot, database)

        # Initialize handlers
        handlers = BotHandlers(database, workout_manager, reminder_manager)

        # Add error handler
        async def error_handler(update, context):
            logging.error(f"Error occurred: {context.error}")
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "Произошла ошибка. Пожалуйста, попробуйте еще раз или начните сначала с помощью /start"
                )

        application.add_error_handler(error_handler)

        # Add handlers to application
        for handler in handlers.get_handlers():
            application.add_handler(handler)

        # Set up commands
        application.job_queue.run_once(setup_commands, when=0)

        # Start the bot
        print("Bot started...")
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,  # Handle pending updates here instead
            close_loop=False  # Prevent multiple event loop issues
        )

    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()