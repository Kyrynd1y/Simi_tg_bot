import random
import sqlite3
import time

import openai
import telegram

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import data
from db_session import *

BOT_TOKEN = '5696148795:AAHWPX9GKwZjfNKkOgoGEBMckqn2tQcgjDQ'
openai.api_key = "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"

cities_lst = []
used_cities_list = []
part_of_game_markup = ['/stop_play']
games_markup = ReplyKeyboardMarkup([['сыграем в города', 'цу-е-фа', 'загадай загадку'] + part_of_game_markup])
tsuefa_markup = ReplyKeyboardMarkup([data.tsuefa + part_of_game_markup])
quit_markup = ReplyKeyboardMarkup([['/talk', '/play', '/images', '/stop']])
talk_markup = ReplyKeyboardMarkup([['/stop_talk']])
riddles_markup = ReplyKeyboardMarkup([['узнать ответ'] + part_of_game_markup])
images_purgat_markup = ReplyKeyboardMarkup([['/bot', '/top_images']])
LAST_LETTER = 'last_letter'
ANSWER = 'answer'
COUNT_ANSWERS = 'COUNT_ANSWERS'
riddles_level = 1
count_correct_answer = 0

global_init("../data/riddles.db")
db_sess = create_session()

bot = telegram.Bot(BOT_TOKEN)


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

    if message[0] != context.user_data[LAST_LETTER]:
        await update.message.reply_text('Первая буква вашего города не совпадает с последней буквой моего города!')
        return 'cities'
    elif message in used_cities_list:
        await update.message.reply_text('Этот город уже был назван!')
        return 'cities'
    elif message not in cities_lst:
        await update.message.reply_text('Я не знаю такого города!')
        return 'cities'
    context.user_data[LAST_LETTER] = message[-1]
    cities_lst.remove(message)
    used_cities_list.append(message)
    chosen_city = random.choice(cities_lst)
    while chosen_city[0] != context.user_data[LAST_LETTER]:
        chosen_city = random.choice(cities_lst)
    used_cities_list.append(chosen_city)
    cities_lst.remove(chosen_city)
    context.user_data[LAST_LETTER] = chosen_city[-1]
    chosen_city[0].upper()
    await update.message.reply_text(chosen_city.capitalize())
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


async def images(update, context):
    await update.message.reply_text('откуда вы хотите получить изображение?', reply_markup=images_purgat_markup)


async def generate_images(update, context):
    await update.message.reply_text('еще в разработке...')
    # так же надо будет объяснить, как писать команды про топы и поиск по ключам


async def db_images(update, context):
    await update.message.reply_text('по какому принципу вы хотите получить изображения?')
    return 'sorting'


async def images_sort_message(update: Update, context):
    command = update.message.text
    if 'топ' in command:
        await top_images(update)
    if command == '':
        pass


async def top_images(update: Update):
    command = update.message.text
    count_top = int(command[command.find('топ') + 3:].strip())
    db_sess.query(Image).order_by(Image.rating)
    selected_images = db_sess.query(Image)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Наш сайт', callback_data='')]])
    for i in range(count_top):
        link = db_sess.query(Image.link)[i][0]
        await bot.send_photo(update.message.chat.id, photo=open(link, 'rb'), reply_markup=keyboard)


def make_a_riddles():
    return random.choice(data.riddles[riddles_level - 1])


async def riddles_func(update, context):
    global riddles_level
    command = update.message.text.lower()
    if command == "узнать ответ":
        context.user_data[COUNT_ANSWERS] += 1
        await update.message.reply_text(context.user_data[ANSWER])
    elif command == context.user_data[ANSWER]:
        context.user_data[COUNT_ANSWERS] += 1
        await update.message.reply_text('Верно!')
    else:
        await update.message.reply_text('Неверно(')
        return 'riddles'
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
        await update.message.reply_text(data.cities_rules,
                                        reply_markup=ReplyKeyboardMarkup([part_of_game_markup]))
        cities_lst = data.cities_lst.copy()
        await update.message.reply_text("я начну")
        chosen_city = random.choice(cities_lst)
        used_cities_list.append(chosen_city)
        cities_lst.remove(chosen_city)
        context.user_data[LAST_LETTER] = chosen_city[-1]
        await update.message.reply_text(chosen_city.capitalize())
        return 'cities'
    elif command == 'цу-е-фа':
        await update.message.reply_text(data.tsuefa_rules,
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
        await update.message.reply_text(data.qst_rules,
                                        reply_markup=riddles_markup)
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

    conv_handler_top_images = ConversationHandler(

        entry_points=[CommandHandler('top_images', db_images)],

        states={
            'sorting': [MessageHandler(filters.TEXT & ~filters.COMMAND, images_sort_message)]
        },

        fallbacks=[CommandHandler('exit', start)]
    )
    application.add_handler(CommandHandler('images', images))
    application.add_handler(CommandHandler('bot', generate_images))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(conv_handler_player)
    application.add_handler(conv_handler_talker)
    application.add_handler(conv_handler_top_images)
    application.run_polling()


if __name__ == '__main__':
    main()
