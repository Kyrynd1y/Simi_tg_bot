import random
import sqlite3
import time

import openai
import requests
import telegram

import dotenv
import os
import replicate

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackQueryHandler
import data
from db_session import *

openai.api_key = "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"

dotenv.load_dotenv()
BOT_TOKEN = os.getenv('REPLICATE_API_TOKEN')

cities_lst = []
used_cities_list = []
part_of_game_markup = ['/stop_play']
exit = ['/exit']
games_markup = ReplyKeyboardMarkup([['сыграем в города', 'цу-е-фа', 'загадай загадку'] + part_of_game_markup])
tsuefa_markup = ReplyKeyboardMarkup([data.tsuefa + part_of_game_markup])
quit_markup = ReplyKeyboardMarkup([['/talk', '/play', '/images', '/stop']])
talk_markup = ReplyKeyboardMarkup([['/stop_talk']])
riddles_markup = ReplyKeyboardMarkup([['узнать ответ'] + part_of_game_markup])
images_purgat_markup = ReplyKeyboardMarkup([['сгенерировать', 'топ картинок'] + exit])
scrolling_images_markup = InlineKeyboardMarkup([[InlineKeyboardButton('👍', callback_data='like'),
                                                 InlineKeyboardButton('download', callback_data='download'),
                                                 InlineKeyboardButton('👎', callback_data='dislike')], [
                                                    InlineKeyboardButton('◀', callback_data='back'),
                                                    InlineKeyboardButton('...', callback_data='...'),
                                                    InlineKeyboardButton('▶', callback_data='forward')]])
top_images_markup = ReplyKeyboardMarkup([["топ 2", "топ 3", "рандомно"] + exit])

LAST_LETTER = 'last_letter'
ANSWER = 'answer'
COUNT_ANSWERS = 'COUNT_ANSWERS'
NUMBER_LINK = 'NUMBER_LINK'
MAX_COUNT_LINK = 'MAX_COUNT_LINK'
USER_ID = 'USER_ID'
MESSAGE_ID = 'MESSAGE_ID'
LINKS = 'LINKS'
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
    return 'purgat'


async def return_images(update, context):
    command = update.message.text
    if command == 'топ картинок':
        await purgatory_images(update, context)
        return 'sorting'
    await update.message.reply_text('Рисую картинку! Это не займет много времени')
    print(command)
    output = replicate.run(
        "ai-forever/kandinsky-2:r8_1OWomDah0wmzZ1L2stFh6UZhuS4uYhP2i4ZZ5",
        input={"prompt": f"{command}, 4k photo"}
    )
    img_data = requests.get(*output).content
    link = f'../data/images/{"_".join(command.split())}.jpg'
    image = Image(key_word=f'{command.split()[0]}', link=link, rating=0)
    db_sess.add(image)
    db_sess.commit()
    with open(link, 'wb') as handler:
        handler.write(img_data)
    await bot.send_photo(update.message.chat.id, photo=img_data)
    await update.message.reply_text('Готово! Нарисовать еще что-нибудь?')
    return 'generate'


async def purgatory_images(update, context):
    if update.message.text == 'топ картинок':
        await update.message.reply_text('по какому принципу вы хотите получить изображения?', reply_markup=top_images_markup)
        context.user_data[NUMBER_LINK] = 0
        return 'sorting'
    elif update.message.text == 'сгенерировать':
        await update.message.reply_text('Что хотите видеть на картинке? Введите точный запрос на английском языке')
        return 'generate'
    else:
        await update.message.reply_text('Я не знаю такую команду')
        return 'purgat'


async def images_sort_message(update: Update, context):
    command = update.message.text
    print(command, 'топ' in command)
    if command == 'сгенерировать':
        await purgatory_images(update, context)
        return 'generate'
        # работает не правильно
    if 'топ' in command:
        count_top = int(command[command.find('топ') + 3:].strip())
        context.user_data[MAX_COUNT_LINK] = count_top - 1
        links = get_links(count_top)
        context.user_data[LINKS] = links
    elif command == 'рандомно':
        context.user_data[MAX_COUNT_LINK] = 0
        links = get_links(command)
        print('links', links)
        context.user_data[LINKS] = links
    else:
        await update.message.reply_text('Я не знаю такую команду')
        return 'sorting'
    await bot.send_photo(update.message.chat.id, photo=open(links[context.user_data[NUMBER_LINK]], 'rb'),
                         reply_markup=scrolling_images_markup)
    context.user_data[MESSAGE_ID] = update.inline_query
    return 'scrolling'


async def scrolling_images(update: Update, context):
    query = update.callback_query
    print('query', query)
    if update.message.text == 'сгенерировать':
        await purgatory_images(update, context)
        return 'generate'
    if query.data == 'like':
        db_sess.query(Image).filter(Image.id == str(context.user_data[NUMBER_LINK] + 1)).first().rating += 1
        db_sess.commit()
    elif query.data == 'dislike':
        db_sess.query(Image).filter(Image.id == str(context.user_data[NUMBER_LINK] + 1)).first().rating -= 1
        db_sess.commit()
    elif query.data == 'back' and context.user_data[NUMBER_LINK] != 0:
        context.user_data[NUMBER_LINK] -= 1
    elif query.data == 'forward' and context.user_data[NUMBER_LINK] != context.user_data[MAX_COUNT_LINK]:
        context.user_data[NUMBER_LINK] += 1
    link = context.user_data[LINKS][context.user_data[NUMBER_LINK]]
    media = telegram.InputMediaPhoto(media=open(link, 'rb'))
    await query.message.edit_media(media=media, reply_markup=scrolling_images_markup)


def get_links(command):
    links = []
    db_sess.query(Image).order_by(Image.rating)
    if type(command) == int:
        for i in range(command):
            links.append(db_sess.query(Image.link)[i][0])
        db_sess.flush()
        db_sess.commit()
    if command == 'рандомно':
        max_images = max(db_sess.query(Image.id))[0]
        print(max_images)
        id_image = random.randint(0, int(max_images))
        links.append(db_sess.query(Image.link)[id_image][0])
    return links


async def next_image(update, context):
    await update.message


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
    context.user_data[USER_ID] = update.message.chat_id
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
    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('start', start)],
    #     states={
    #         'FIRST': [CallbackQueryHandler(scrolling_images)]
    #     },
    #     fallbacks=[CommandHandler('start', start)]
    # )
    conv_handler_images = ConversationHandler(
        entry_points=[CommandHandler('images', images)],

        states={
            'purgat': [MessageHandler(filters.TEXT & ~filters.COMMAND, purgatory_images)],
            'generate': [MessageHandler(filters.TEXT & ~filters.COMMAND, return_images)],
            'sorting': [MessageHandler(filters.TEXT & ~filters.COMMAND, images_sort_message)],
            'scrolling': [CallbackQueryHandler(scrolling_images)]
        },
        fallbacks=[CommandHandler('exit', start)]
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(conv_handler_player)
    application.add_handler(conv_handler_talker)
    application.add_handler(conv_handler_images)
    application.run_polling()


if __name__ == '__main__':
    main()
