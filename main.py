from dotenv import load_dotenv
import os
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackContext, Filters

from data_handler import DataHandler

load_dotenv()

API_KEY = os.environ.get('PEEPOLEAVEBOT_API_KEY')
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

data_handler = DataHandler()

NAME, LINK = 0, 1


def start(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.first_name
    data_handler.add_user(update.message.chat_id)

    update.message.reply_sticker('CAACAgQAAxkBAAED-thiE6kHCRXdas7kVJsioqUyEk6JLAACMwEAAqghIQaDngab6f9thSME')
    update.message.reply_text(
        f'Hello {username}!\n'
        f'I am the OLX Notifier bot and I will notify you about new offers on OLX.\n'
        f'Available commands:\n'
        f'/start\t - to get help\n'
        f'/help\t - to contact my creator\n'
        f'/add\t - to add new item to your list\n'
        f'/set\t - to set the timer\n'
        f'/unset\t - to unset the timer\n'
        f'/delete\t - to delete a record from your list\n'
        f'/mydata\t - to see your list fo items\n',
        parse_mode='HTML')


def add(update: Update, context: CallbackContext) -> int:
    """Adds a new item to search for"""
    update.message.reply_sticker('CAACAgQAAxkBAAED-t9iE7RwHrtiBrcDDjDIuhCOqWwHOAACTAEAAqghIQZjKrRWscYWyCME')
    update.message.reply_text(
        'All right!\n'
        'First of all, send me the name of an item you wish to add.')

    return NAME


def add_name(update: Update, context: CallbackContext) -> int:
    """Stores the name of the new item"""
    context.user_data['new_name'] = update.message.text

    update.message.reply_text(
        'Thank you!'
        ' Now you can send me the link to the item or you can send "no link" and I will create one myself.',
        parse_mode='HTML'
    )

    return LINK


def add_link(update: Update, context: CallbackContext) -> int:
    """Stores the url to the new item"""
    chat_id = update.message.chat_id
    name = context.user_data['new_name']
    url = update.message.text
    if url.startswith('no link'):
        url = f'https://www.olx.pl/poznan/q-{name}/'

    data = data_handler.get_data_by_id(chat_id)
    data[name] = {"Number": 0, "Url": url}
    data_handler.update_user_data(chat_id, data)
    update.message.reply_text(f'Successfully added {name} to the database.')

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    update.message.reply_text('Okay. Back to the main menu. Press /start to begin.', parse_mode='HTML')

    return ConversationHandler.END


def delete(update: Update, context: CallbackContext):
    """Allows the user to delete data"""
    chat_id = update.message.chat_id

    name = context.args[0]
    text = data_handler.delete_data(chat_id, name)
    update.message.reply_text(text, parse_mode='MarkdownV2')


def main() -> None:
    updater = Updater(API_KEY)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            NAME: [MessageHandler(Filters.regex(r"^(?!\/cancel$)"), add_name)],
            LINK: [MessageHandler(Filters.regex(r"^(https:\/\/.*olx.pl\/.*|no link)$"), add_link)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]))

    # dispatcher.add_handler(CommandHandler("set", set_timer))
    # dispatcher.add_handler(CommandHandler("unset", unset))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
