from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler
import logging

from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
MAIN_MENU, VOTE_CREATION, VOTE_SELECTION = range(3)


def send_hello(bot, update):
    reply_keyboard = [['create', 'select']]
    bot.send_message(chat_id=update.message.chat_id, text="hello mah dewd",
                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MAIN_MENU


def cancel(bot, update):
    return MAIN_MENU


def main_menu(bot: Bot, update: Update):
    user = update.message.from_user
    if update.message.text == 'create':
        logger.info(f'User {user.id} wanted to create voting')
        bot.send_message(chat_id=update.message.chat_id, text='Okay')
        return VOTE_CREATION
    if update.message.text == 'select':
        logger.info(f'User {user.id} wanted to select voting')
        bot.send_message(chat_id=update.message.chat_id, text='Okay')
        return VOTE_SELECTION
    return None


updater = Updater('560433922:AAHzL-izLbi3EZNHbPuDCy-9ckefnb3D7rE')
dispatcher = updater.dispatcher
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', send_hello)],

    states={
        MAIN_MENU: [RegexHandler('^(create|select)$', main_menu)],

        VOTE_CREATION: [MessageHandler(Filters.text, )],

        VOTE_SELECTION: [],
    },

    fallbacks=[CommandHandler('cancel', cancel)]
)
dispatcher.add_handler(conv_handler)
updater.start_polling()

# manager = VotingManager((127, 0, 0, 1), 14228)
# voting = manager.create_new_voting(['путин', 'нэвэльный'], 1337)
# for can in voting.get_all_candidates():
#     print(can)
# print('-' * 10)
# voting.vote_and_get_results(0, 0)
# voting.vote_and_get_results(0, 0)
# voting.vote_and_get_results(0, 1)
# voting.vote_and_get_results(12, 1)
#
# print('-' * 10)
# print(voting.finalize(0))
# print('-' * 10)
# for can, vot in voting.finalize(1337):
#     print(f"{can}: {vot}")
