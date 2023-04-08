import logging
import random
import time

import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import data

BOT_TOKEN = '5696148795:AAHWPX9GKwZjfNKkOgoGEBMckqn2tQcgjDQ'
openai.api_key = "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"

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
# )
#
# logger = logging.getLogger(__name__)

cities_lst = []
part_of_game_markup = ['/stop_play']
games_markup = ReplyKeyboardMarkup([['сыграем в города', 'цу-е-фа', 'загадай загадку'] + part_of_game_markup])
tsuefa_markup = ReplyKeyboardMarkup([data.tsuefa + part_of_game_markup])
quit_markup = ReplyKeyboardMarkup([['/talk', '/play', '/stop']])
talk_markup = ReplyKeyboardMarkup([['/stop_talk']])
LAST_LETTER = 'last_letter'
ANSWER = 'answer'
COUNT_ANSWERS = 'COUNT_ANSWERS'
riddles_level = 1
count_correct_answer = 0

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


async def send(update, context):
    command = update.message.text
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=command,
        temperature=0.9,
        max_tokens=3000,
        top_p=0.7,
        frequency_penalty=0.0
    )
    await update.message.reply_text(response['choices'][0]['text'])
    return 'continue'


async def game_cities(update, context):
    message = update.message.text.lower().strip()
    print('game_cities')
    if message not in cities_lst:
        await update.message.reply_text('Я не знаю такого города')
        return 'cities'
    elif message[0] != context.user_data[LAST_LETTER]:
        await update.message.reply_text('Первая буква вашего города не совпадает с последней буквой моего города')
        return 'cities'
    context.user_data[LAST_LETTER] = message[-1]
    cities_lst.remove(message)
    chosen_city = random.choice(cities_lst)
    while chosen_city[0] != context.user_data[LAST_LETTER]:
        chosen_city = random.choice(cities_lst)
    cities_lst.remove(chosen_city)
    context.user_data[LAST_LETTER] = chosen_city[-1]
    await update.message.reply_text(chosen_city)
    return 'cities'


async def tsuefa(update, context):
    # сделать клавиатуру с выбором ответа
    message = update.message.text
    bot_tsuefa = context.user_data['tsuefa']
    if bot_tsuefa == message:
        await update.message.reply_text('ничья', reply_markup=ReplyKeyboardMarkup([data.tsuefa + ['/talk']]))
    elif (bot_tsuefa == 'камень' and message == 'ножницы') or (bot_tsuefa == 'ножницы' and message == 'бумага') or (
            bot_tsuefa == 'бумага' and message == 'камень'):
        await update.message.reply_text('я выиграл!)', reply_markup=tsuefa_markup)
    else:
        await update.message.reply_text('вы выиграли!',
                                        reply_markup=tsuefa_markup)
    time.sleep(2)
    await update.message.reply_text('цу')
    time.sleep(1)
    await update.message.reply_text('е')
    time.sleep(1)
    await update.message.reply_text('фа')
    bot_tsuefa = random.choice(data.tsuefa)
    context.user_data['tsuefa'] = bot_tsuefa
    await update.message.reply_text(bot_tsuefa)
    return 'tsuefa'


def make_a_riddles():
    return random.choice(data.riddles[riddles_level])


async def riddles_func(update, context):
    global riddles_level
    command = update.message.text
    if command == context.user_data[ANSWER]:
        context.user_data[COUNT_ANSWERS] += 1
        await update.message.reply_text('Верно!')
    if context.user_data[COUNT_ANSWERS] == 3 and riddles_level != 2:
        riddles_level += 1
    riddle = make_a_riddles()
    await update.message.reply_text(riddle['riddle'])
    context.user_data[ANSWER] = riddle[ANSWER]
    return 'riddles'


async def purgatory(update, context):
    global cities_lst
    command = update.message.text.lower()
    print(command)
    if command == 'сыграем в города':
        await update.message.reply_text('объяснение правил игры...',
                                        reply_markup=ReplyKeyboardMarkup([part_of_game_markup]))
        cities_lst = data.cities_lst.copy()
        await update.message.reply_text("я начну")
        chosen_city = random.choice(cities_lst)
        cities_lst.remove(chosen_city)
        context.user_data[LAST_LETTER] = chosen_city[-1]
        await update.message.reply_text(chosen_city)
        return 'cities'
    elif command == 'цу-е-фа':
        await update.message.reply_text('объяснение правил игры...',
                                        reply_markup=tsuefa_markup)
        time.sleep(5)
        await update.message.reply_text('цу')
        time.sleep(1)
        await update.message.reply_text('е')
        time.sleep(1)
        await update.message.reply_text('фа')
        bot_choise = random.choice(data.tsuefa)
        context.user_data['tsuefa'] = bot_choise
        await update.message.reply_text(bot_choise)
        return 'tsuefa'
    elif command == 'загадай загадку':
        await update.message.reply_text('объяснение правил игры...',
                                        reply_markup=ReplyKeyboardMarkup([part_of_game_markup]))
        riddle = make_a_riddles()
        await update.message.reply_text(riddle['riddle'])
        context.user_data[ANSWER] = riddle['answer']
        context.user_data[COUNT_ANSWERS] = 0
        return 'riddles'


async def stop(update, context):
    print('stop')
    await update.message.reply_text("До встречи в чате!", reply_markup=ReplyKeyboardMarkup([['/start']]))


async def start_games(update, context):
    await update.message.reply_text('в какую игру сыграем?', reply_markup=games_markup)
    return 'purgatory'


async def talking(update, context):
    await update.message.reply_text('давай поговорим)', reply_markup=talk_markup)
    return 'continue'


async def start(update, context):
    await update.message.reply_text('чем займемся?', reply_markup=quit_markup)
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler_player = ConversationHandler(

        entry_points=[CommandHandler('play', start_games)],

        states={
            'cities': [MessageHandler(filters.TEXT & ~filters.COMMAND, game_cities)],
            'tsuefa': [MessageHandler(filters.TEXT & ~filters.COMMAND, tsuefa)],
            'purgatory': [MessageHandler(filters.TEXT & ~filters.COMMAND, purgatory)],
            'riddles': [MessageHandler(filters.TEXT & ~filters.COMMAND, riddles_func)]

        },

        fallbacks=[CommandHandler('stop_play', start)]
    )
    conv_handler_talker = ConversationHandler(

        entry_points=[CommandHandler('talk', talking)],

        states={
            'continue': [MessageHandler(filters.TEXT & ~filters.COMMAND, send)],
        },

        fallbacks=[CommandHandler('stop_talk', start)]
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(conv_handler_player)
    application.add_handler(conv_handler_talker)
    application.run_polling()


if __name__ == '__main__':
    main()
