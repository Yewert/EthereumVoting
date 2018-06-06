import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

from typing import Dict

from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler, Filters, MessageHandler

from backend.VotingBuilder import VotingBuilder, Voting
from backend.VotingManager import VotingManager

logger = logging.getLogger(__name__)
builders: Dict[int, VotingBuilder] = {}
currently_modified_votings: Dict[int, Voting] = {}
VOTING_MANAGER = VotingManager((127, 0, 0, 1), 14228)
CANDIDATE_NAME_LENGTH = 30
MAIN_MENU, VOTING_CREATION, VOTING_SELECTION, VOTING_MANAGEMENT = range(4)
MAIN_MENU_KEYBOARD = [['create'], ['select']]


def send_hello(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="hello mah dewd",
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def error(bot, chat_id, state, message, **botkwagrgs):
    bot.send_message(chat_id=chat_id, text=f'Something went wrong: {message}', **botkwagrgs)
    return state


def error_to_menu(bot, chat_id, message):
    return error(bot, chat_id, MAIN_MENU, message,
                 reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))


def unsupported_action(bot, update):
    chat_id = update.message.chat_id
    if update.message.from_user.id in builders:
        del builders[update.message.from_user.id]
    if update.message.from_user.id in currently_modified_votings:
        del currently_modified_votings[update.message.from_user.id]
    return error_to_menu(bot, chat_id, 'unsupported action')


def cancel(bot, update):
    if update.message.from_user.id in builders:
        del builders[update.message.from_user.id]
    if update.message.from_user.id in currently_modified_votings:
        del currently_modified_votings[update.message.from_user.id]
    bot.send_message(chat_id=update.message.chat_id, text='Canceled',
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def finalize_creation(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in builders:
        return error(bot, chat_id, VOTING_CREATION, 'try to add some candidates first')
    res = builders[user.id].get_voting()
    del builders[user.id]
    if not res:
        return error_to_menu(bot, chat_id, 'voting creation failed')
    candidates = res.get_candidates()
    if not candidates:
        return error_to_menu(bot, chat_id, 'candidates extraction failed')
    candidates = '\n'.join(candidates)
    logger.info(f'User {user.id} created new voting at address {res.address}')
    bot.send_message(chat_id=chat_id, text=f"Here's your vote:\n{candidates}")
    bot.send_message(chat_id=chat_id, text=res.address,
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def voting_creation(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in builders:
        builders[user.id] = VotingBuilder(user.id, VOTING_MANAGER)
    if len(update.message.text) > CANDIDATE_NAME_LENGTH:
        return error(bot, chat_id, VOTING_CREATION, f'line too long ({CANDIDATE_NAME_LENGTH} characters is max)')
    if builders[user.id].contains(update.message.text):
        error(bot, chat_id, VOTING_CREATION, 'duplicate candidates are not allowed')
    status = builders[user.id].add_candidate(update.message.text)
    if not status:
        return error(bot, chat_id, VOTING_CREATION, 'candidate list is full\n use /end to finalize voting creation')
    bot.send_message(chat_id=chat_id, text=f'Added candidate "{update.message.text}" to list')
    return VOTING_CREATION


def voting_selection(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    voting = VOTING_MANAGER.get_voting_from_address(update.message.text)
    if not voting:
        logger.warning(f'User {user.id} tried to access wrong address {update.message.text}')
        return error_to_menu(bot, chat_id, 'wrong address')
    currently_modified_votings[user.id] = voting
    candidates = voting.get_candidates()
    if not candidates:
        raise NotImplementedError
    candidates_str = '\n'.join(candidates)
    bot.send_message(chat_id=chat_id, text=f"Here's a list of candidates\n"
                                           f"{candidates_str}\n"
                                           f"You can /view results\n"
                                           f"You can also /finalize voting (active only for owner)")
    voted = voting.has_voted(user.id)
    if voted is None:
        raise NotImplementedError
    if not voted:
        keyb = [[candidate] for candidate in candidates]
        bot.send_message(chat_id=chat_id,
                         text='Seems like you haven\'t voted yet!\nYou can choose candidate on the keyboard',
                         reply_markup=ReplyKeyboardMarkup(keyb, one_time_keyboard=True))
    return VOTING_MANAGER


def vote(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in currently_modified_votings:
        raise NotImplementedError
    voting = currently_modified_votings[user.id]
    voted = voting.has_voted(user.id)
    if voted is None:
        del currently_modified_votings[user.id]
        return error_to_menu(bot, chat_id,
                             'contract interaction error.\nThere\'s high chance that owner finalized this voting')
    if voted:
        return error(bot, chat_id, VOTING_MANAGER, 'you have already voted!')
    candidates = voting.get_candidates()
    if not candidates:
        del currently_modified_votings[user.id]
        return error_to_menu(bot, chat_id,
                             'contract interaction error.\nThere\'s high chance that owner finalized this voting')
    try:
        ind = candidates.index(update.message.text)
    except ValueError:
        return error(bot, chat_id, VOTING_MANAGER, 'candidate not present in the list')
    res = voting.vote_and_get_results(user.id, ind)
    if not res:
        raise NotImplementedError
    res_str = '\n'.join((f'{candidate} : {votes}' for candidate, votes in res))
    bot.send_message(chat_id=chat_id, text=f'{voting.address}\n{res_str}')
    return VOTING_MANAGER


def finalize_voting(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in currently_modified_votings:
        raise NotImplementedError
    voting = currently_modified_votings[user.id]
    address = voting.address
    res = voting.finalize(user.id)
    if not res:
        return error(bot, chat_id, VOTING_MANAGER, 'you are not the owner of this voting!')
    del currently_modified_votings[user.id]
    res_str = '\n'.join((f'{candidate} : {votes}' for candidate, votes in res))
    bot.send_message(chat_id=chat_id,
                     text=f'Voting at adress:\n{address}\nsuccessfully finalized.\nHere\'s the results\n{res_str}',
                     reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True))
    return MAIN_MENU


def view_results(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    if user.id not in currently_modified_votings:
        raise NotImplementedError
    voting = currently_modified_votings[user.id]
    address = voting.address
    res = voting.get_candidates_votes()
    if not res:
        del currently_modified_votings[user.id]
        return error_to_menu(bot, chat_id,
                             'contract interaction error.\nThere\'s high chance that owner finalized this voting')
    res_str = '\n'.join((f'{candidate} : {votes}' for candidate, votes in res))
    bot.send_message(chat_id=chat_id, text=f'{address}\n{res_str}')
    return VOTING_MANAGER


def main_menu(bot: Bot, update: Update):
    user = update.message.from_user
    if update.message.text == 'create':
        logger.info(f'User {user.id} wanted to create voting')
        bot.send_message(chat_id=update.message.chat_id,
                         text='Enter candidates one by one (10 is max)\nUse /end to finalize voting creation')
        return VOTING_CREATION
    if update.message.text == 'select':
        logger.info(f'User {user.id} wanted to select voting')
        bot.send_message(chat_id=update.message.chat_id, text='Type in your voting address')
        return VOTING_SELECTION
    return None


updater = Updater('')
dispatcher = updater.dispatcher

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', send_hello)],

    states={
        MAIN_MENU: [RegexHandler('^(create|select)$', main_menu)],

        VOTING_CREATION: [CommandHandler('end', finalize_creation), MessageHandler(Filters.text, voting_creation)],

        VOTING_SELECTION: [RegexHandler('^0x[0-9A-Fa-f]+$', voting_selection)],
        VOTING_MANAGER: [CommandHandler('view', view_results), CommandHandler('finalize', finalize_voting),
                         MessageHandler(Filters.text, vote)]
    },

    fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.all, unsupported_action)]
)
dispatcher.add_handler(conv_handler)
logger.info('Running')
updater.start_polling()
