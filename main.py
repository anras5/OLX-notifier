from dotenv import load_dotenv
import os
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

load_dotenv()

API_KEY = os.environ.get('API_KEY')
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')
PORT = int(os.environ.get('PORT', '8443'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    username = update.message.from_user.first_name

    update.message.reply_text(f"Hello from PyCharm, {username}")


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    chat_id = job.context
    text = 'I am alive!'
    if text:
        context.bot.send_message(job.context, text=text)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    try:
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('Sorry, we can not go back to the past!')
            return

        is_job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(alarm, interval=due, context=chat_id, name=str(chat_id))

        text = 'Timer successfully set!'
        if is_job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError) as e:
        update.message.reply_text(f'Usage: /set <seconds> {e}')


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def main() -> None:
    updater = Updater(API_KEY)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("unset", unset))

    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=API_KEY,
                          webhook_url='https://olx-notifier-v2.herokuapp.com/' + API_KEY)
    updater.idle()


if __name__ == '__main__':
    main()
