from telegram.ext import ApplicationBuilder, MessageHandler, filters

from cfg.config import settings
from services.bot import Bot
from utils.logs import log


def start_bot():
    try:
        app = ApplicationBuilder().token(settings.TG_TOKEN).read_timeout(7).get_updates_read_timeout(42).build()
        message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, Bot.handle_message)
        app.add_handler(message_handler)

        log.info("Bot is running and listening")
        app.run_polling()
    except BaseException as e:
        log.info(f"Bot Error: {e}")
        start_bot()


def main():
    log.info("Bot is starting ...")
    start_bot()  # starting bot
    log.info("Bot is shut down")


if __name__ == '__main__':
    main()
