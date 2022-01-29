from dotenv import load_dotenv
import os
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

load_dotenv()

API_KEY = os.environ.get('API_KEY')
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.first_name

    update.message.reply_text(f"Hello from PyCharm, {username}")


def main() -> None:
    updater = Updater(API_KEY)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
