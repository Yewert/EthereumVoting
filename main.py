import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
from typing import Dict

from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler

from backend.VotingBuilder import VotingBuilder
from backend.VotingManager import VotingManager

logger = logging.getLogger(__name__)
builders: Dict[int, VotingBuilder] = {}
VOTING_MANAGER = VotingManager((127, 0, 0, 1), 14228)
CANDIDATE_NAME_LENGTH = 30
MAIN_MENU, VOTE_CREATION, VOTE_SELECTION = range(3)
MAIN_MENU_KEYBOARD = [['create'], ['select']]


def send_hello(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="hello mah dewd",
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def error(bot, chat_id, state, message, **botkwagrgs):
    bot.send_message(chat_id=chat_id, text=f'Something went wrong: {message}', **botkwagrgs)
    return state


def cancel(bot, update):
    if update.message.from_user.id in builders:
        del builders[update.message.from_user.id]
    bot.send_message(chat_id=update.message.chat_id, text='Canceled',
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def finalize_creation(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in builders:
        return error(bot, chat_id, VOTE_CREATION, 'try to add some candidates first')
    res = builders[user.id].get_voting()
    del builders[user.id]
    candidates = res.get_all_candidates()
    if not candidates:
        return error(bot, chat_id, MAIN_MENU, 'candidates extraction failed',
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    candidates = '\n'.join(candidates)
    logger.info(f'User {user.id} created new voting at address {res.address}')
    bot.send_message(chat_id=chat_id, text=f"Here's your vote:\n{res.address}\n{candidates}",
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def vote_creation(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in builders:
        builders[user.id] = VotingBuilder(user.id, VOTING_MANAGER)
    if len(update.message.text) > CANDIDATE_NAME_LENGTH:
        return error(bot, chat_id, VOTE_CREATION, f'line too long ({CANDIDATE_NAME_LENGTH} characters is max)')
    status = builders[user.id].add_candidate(update.message.text)
    if not status:
        return error(bot, chat_id, VOTE_CREATION, 'candidate list is full\n use /end to finalize voting creation')
    bot.send_message(chat_id=chat_id, text=f'Added candidate "{update.message.text}" to list')
    return VOTE_CREATION


def main_menu(bot: Bot, update: Update):
    user = update.message.from_user
    if update.message.text == 'create':
        logger.info(f'User {user.id} wanted to create voting')
        bot.send_message(chat_id=update.message.chat_id,
                         text='Enter candidates one by one (10 is max)\nUse /end to finalize voting creation')
        return VOTE_CREATION
    if update.message.text == 'select':
        logger.info(f'User {user.id} wanted to select voting')
        bot.send_message(chat_id=update.message.chat_id, text='Not supported yet',
                         reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
        return MAIN_MENU
    return None


updater = Updater('560433922:AAHzL-izLbi3EZNHbPuDCy-9ckefnb3D7rE')
dispatcher = updater.dispatcher
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', send_hello)],

    states={
        MAIN_MENU: [RegexHandler('^(create|select)$', main_menu)],

        VOTE_CREATION: [CommandHandler('end', finalize_creation), MessageHandler(Filters.text, vote_creation)],

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
