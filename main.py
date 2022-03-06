import os
import logging
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackContext, Filters

from olx_notifier import message_maker
from data_handler import DataHandler
from link_creator import LinkCreator
from keep_alive import keep_alive

load_dotenv()

API_KEY = os.environ.get('API_KEY')
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

data_handler = DataHandler()
link_creator = LinkCreator()

NAME, LINK, LOCATION, DISTANCE, PRICE, ADD_PRICE_TO, CATEGORY = range(7)
LOCATIONS = ['Poland', 'Poznan', 'Warszawa']
DISTANCES = ['0', '5', '10', '15', '30', '50', '75', '100']
PRICES_FROM = ['0', '100',
               '200', '500',
               '750', '1000',
               '1500', '2000',
               '3000', '5000']
PRICES_TO = ['0', '500',
             '1000', '1500',
             '2000', '3000',
             '5000', '10000',
             '15000', '20000']
CATEGORIES = {
    'Motoryzacja': 'motoryzacja',
    'Samochody': 'motoryzacja/samochody',
    'Motorki': 'motoryzacja/motocykle-skutery',
    'Instrumenty': 'muzyka-edukacja/instrumenty',
    'Pozostałe': 'oferty'
}
SECONDS = 20


def is_in_database(func):
    """Wrapper for adding user to the database"""

    def wrap(*args, **kwargs):
        update = args[0]
        if not data_handler.is_user_in_database(update.message.chat_id):
            data_handler.add_user(update.message.chat_id)
        result = func(*args, **kwargs)
        return result

    return wrap


@is_in_database
def start(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.first_name

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
        f'/mydata\t - to see your list of items\n',
        parse_mode='HTML')


@is_in_database
def get_help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f'If you have encountered a problem, a bug or you have an idea how to improve the bot '
        f'contact me via email: anras1filip@gmail.com\n'
        f'Type /start to see available commands.'
    )


@is_in_database
def add(update: Update, context: CallbackContext) -> int:
    """Adds a new item to search for"""
    update.message.reply_sticker('CAACAgQAAxkBAAED-t9iE7RwHrtiBrcDDjDIuhCOqWwHOAACTAEAAqghIQZjKrRWscYWyCME')
    update.message.reply_text(
        'All right!\n'
        'First of all, send me the name of an item you wish to add.\n'
        'Type /cancel to go back.')

    return NAME


def add_name(update: Update, context: CallbackContext) -> int:
    """Stores the name of the new item"""
    context.user_data['name'] = update.message.text

    update.message.reply_text(
        'Thank you!'
        ' Now you can send me the link to the item or you can type "no link" to make one with the creator.',
        reply_markup=ReplyKeyboardMarkup(
            [['no link']],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

    return LINK


def add_link(update: Update, context: CallbackContext) -> int:
    """Stores the url to the new item"""
    chat_id = update.message.chat_id
    name = context.user_data['name']
    url = update.message.text
    if url.lower().startswith('no link'):
        reply_keyboard = [LOCATIONS]
        update.message.reply_text('All right. Then tell me in what location do you want to search.',
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      input_field_placeholder='Choose the location.',
                                      resize_keyboard=True)
                                  )
        return LOCATION
    else:
        data = data_handler.get_data_by_id(chat_id)
        data[name] = {"Number": 0, "Counter": 0, "Url": url}
        data_handler.update_user_data(chat_id, data)
        context.user_data.clear()
        update.message.reply_text(f'Successfully added {name} to the database.')

        return ConversationHandler.END


def add_location(update: Update, context: CallbackContext) -> int:
    """Saves the location of the new item"""
    context.user_data['location'] = update.message.text.lower()
    if update.message.text in LOCATIONS[1:]:
        reply_keyboard = [DISTANCES[x:x + 4] for x in range(0, len(DISTANCES), 4)]
        update.message.reply_text('All right. Now choose the search radius.',
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      input_field_placeholder='Choose the search radius.')
                                  )
        return DISTANCE
    else:
        update.message.reply_text('All right. Now choose the price.\nType FROM-TO range. For example 200-500.',
                                  reply_markup=ReplyKeyboardRemove())
        return PRICE


def add_distance(update: Update, context: CallbackContext) -> int:
    """Saves the search radius"""
    context.user_data['distance'] = update.message.text
    reply_keyboard = [PRICES_FROM[x:x + 2] for x in range(0, len(PRICES_FROM), 2)]
    update.message.reply_text('All right. Now choose the price.\n'
                              'Type FROM-TO range. For example 200-500. Type 0-0 to skip this step.\n'
                              'You can also use buttons to choose FROM price and then TO price.',
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard,
                                  one_time_keyboard=True,
                                  input_field_placeholder='Type FROM-TO price range or choose FROM price.',
                              ))
    return PRICE


def add_price(update: Update, context: CallbackContext) -> int:
    """Saves the price range"""
    message = tuple(map(int, update.message.text.split('-')))
    if len(message) == 1:
        context.user_data['price_from'] = message[0]
        prices_to_display = list(filter(lambda x: int(x) > context.user_data['price_from'], PRICES_TO))
        reply_keyboard = [prices_to_display[x:x + 2] for x in range(0, len(prices_to_display), 2)]
        update.message.reply_text('Now choose the TO price.',
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      input_field_placeholder='Choose TO price.'
                                  ))
        return ADD_PRICE_TO

    else:
        price_from, price_to = map(int, update.message.text.split('-'))

        if price_from > price_to:
            update.message.reply_text('Wrong usage. FROM has to be lower than TO. Try again.')
            return PRICE
        else:
            if price_from == price_to == '0':
                pass
            elif price_from <= price_to:
                context.user_data['price_from'] = price_from
                context.user_data['price_to'] = price_to

            display_categories(update, context)
            return CATEGORY


def add_price_to(update: Update, context: CallbackContext) -> int:
    """Saves the TO price"""
    context.user_data['price_to'] = update.message.text
    display_categories(update, context)
    return CATEGORY


def display_categories(update: Update, context: CallbackContext) -> None:
    categories_show = [x for x in CATEGORIES.keys()]
    reply_keyboard = [categories_show[x:x + 2] for x in range(0, len(categories_show), 2)]

    update.message.reply_text('All right. Last question: Category.',
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard,
                                  one_time_keyboard=True,
                                  input_field_placeholder='Choose category.',
                                  resize_keyboard=True)
                              )


def add_category(update: Update, context: CallbackContext) -> int:
    """Saves the category and uploads gathered information to json"""
    context.user_data['category'] = CATEGORIES[update.message.text]
    name = context.user_data['name']
    url = link_creator.create_link(context.user_data)
    chat_id = update.message.chat_id

    data = data_handler.get_data_by_id(chat_id)
    data[name] = {"Number": 0, "Counter": 0, "Url": url}
    data_handler.update_user_data(chat_id, data)
    update.message.reply_text(f'Successfully added {name} to the database.', reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Okay. Back to the main menu. Press /start to begin.',
                              parse_mode='HTML',
                              reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

    return ConversationHandler.END


@is_in_database
def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    if data_handler.get_data_by_id(chat_id):
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
    else:
        update.message.reply_text('Try adding some data to your list first!')


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


@is_in_database
def delete(update: Update, context: CallbackContext) -> int:
    """Allows the user to delete an item"""
    chat_id = update.message.chat_id

    user_data = data_handler.get_data_by_id(chat_id)
    if user_data:
        names = [name for name in user_data.keys()]
        reply_keyboard = [names[x:x + 2] for x in range(0, len(names), 2)]
        update.message.reply_text('Choose the item you want to delete. Type /cancel to go back.',
                                  reply_markup=ReplyKeyboardMarkup(
                                      reply_keyboard,
                                      one_time_keyboard=True,
                                      input_field_placeholder='Choose the item to delete.',
                                      resize_keyboard=True)
                                  )
        return 0
    else:
        update.message.reply_text('Nothing to delete. Try /add to add an item first.')
        return ConversationHandler.END


def delete_item(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    name = update.message.text
    text = data_handler.delete_data(chat_id, name)
    update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


@is_in_database
def my_data(update: Update, context: CallbackContext):
    """Allows the user to read their data"""
    chat_id = update.message.chat_id

    data = data_handler.get_data_by_id(chat_id)
    text = ""
    for name, values in data.items():
        text += f'{name} -> {values.get("Number")}\n'
    if text:
        update.message.reply_text(f"Your data:\n{text}")
    else:
        update.message.reply_text('Your list is empty. Try adding some items with /add')


def main() -> None:
    updater = Updater(API_KEY)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', get_help))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            NAME: [MessageHandler(Filters.regex(r"^(?!\/)"), add_name)],
            LINK: [MessageHandler(Filters.regex(r"^(https:\/\/.*olx.pl\/.*|(?i)no link)$"), add_link)],
            LOCATION: [MessageHandler(Filters.text(LOCATIONS), add_location)],
            DISTANCE: [MessageHandler(Filters.text(DISTANCES), add_distance)],
            PRICE: [MessageHandler(
                Filters.regex(r"^([0-9]|[0-9][0-9]|[0-9][0-9][0-9]|[0-9][0-9][0-9][0-9]|"
                              r"[0-9][0-9][0-9][0-9][0-9])-([0-9]|[0-9][0-9]|[0-9][0-9][0-9]|"
                              r"[0-9][0-9][0-9][0-9]|[0-9][0-9][0-9][0-9][0-9])$") | Filters.text(PRICES_FROM),
                add_price)],
            ADD_PRICE_TO: [MessageHandler(Filters.text(PRICES_TO), add_price_to)],
            CATEGORY: [MessageHandler(Filters.text(CATEGORIES), add_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],
        states={
            0: [MessageHandler(Filters.regex(r"^(?!\/cancel)$"), delete_item)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    )
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("unset", unset))
    dispatcher.add_handler(CommandHandler('mydata', my_data))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    # keep_alive()
    main()
