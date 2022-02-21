import os
import logging
# from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackContext, Filters

from olx_notifier import message_maker
from data_handler import DataHandler
from keep_alive import keep_alive

# load_dotenv()

API_KEY = os.environ.get('API_KEY')
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

data_handler = DataHandler()

NAME, LINK = 0, 1
SECONDS = 10


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


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Okay. Back to the main menu. Press /start to begin.', parse_mode='HTML')

    return ConversationHandler.END


def delete(update: Update, context: CallbackContext):
    """Allows the user to delete data"""
    chat_id = update.message.chat_id

    name = context.args[0]
    text = data_handler.delete_data(chat_id, name)
    update.message.reply_text(text, parse_mode='MarkdownV2')


def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id

    try:
        due = SECONDS

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(alarm, interval=due, context=chat_id, name=str(chat_id))

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text(f'Sorry :( an error occured. Try again.')


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    chat_id = job.context
    text = message_maker(chat_id)
    if text:
        context.bot.send_message(job.context, text=text)


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def user_data(update: Update, context: CallbackContext):
    """Allows the user to read their data"""
    chat_id = update.message.chat_id

    data = data_handler.get_data_by_id(chat_id)
    text = ""
    for name, values in data.items():
        text += f'{name} -> {values.get("Number")}\n'
    update.message.reply_text(f"Your data:\n{text}")


def main() -> None:
    updater = Updater(API_KEY)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', start))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            NAME: [MessageHandler(Filters.regex(r"^(?!\/cancel$)"), add_name)],
            LINK: [MessageHandler(Filters.regex(r"^(https:\/\/.*olx.pl\/.*|no link)$"), add_link)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]))
    dispatcher.add_handler(CommandHandler('delete', delete))
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("unset", unset))
    dispatcher.add_handler(CommandHandler('mydata', user_data))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    keep_alive()
    main()
