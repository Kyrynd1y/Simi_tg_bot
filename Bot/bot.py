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

dotenv.load_dotenv()
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
BOT_TOKEN = os.getenv('BOT_TOKEN')
openai.api_key = os.getenv('OPENAI_API_KEY')

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
scrolling_images_lst = [[InlineKeyboardButton('👍', callback_data='like'),
                         InlineKeyboardButton('likes...', callback_data='like'),
                         InlineKeyboardButton('👎', callback_data='dislike')], [
                            InlineKeyboardButton('◀', callback_data='back'),
                            InlineKeyboardButton('...', callback_data='...'),
                            InlineKeyboardButton('▶', callback_data='forward')],
                        [InlineKeyboardButton('download', callback_data='download')]]

top_images_markup = ReplyKeyboardMarkup([["топ 3", "топ 5", "топ 10", "рандомно"] + exit])

LAST_LETTER = 'last_letter'
ANSWER = 'answer'
COUNT_ANSWERS = 'COUNT_ANSWERS'
NUMBER_LINK = 'NUMBER_LINK'
MAX_COUNT_LINK = 'MAX_COUNT_LINK'
USER_ID = 'USER_ID'
MESSAGE_ID = 'MESSAGE_ID'
LINKS = 'LINKS'
IS_RANDOM = 'IS_RANDOM'
LST_RANDOM_IMAGES = 'LST_RANDOM_IMAGES'

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
    if message[-1] not in ['ь', 'ъ']:
        context.user_data[LAST_LETTER] = message[-1]
    else:
        context.user_data[LAST_LETTER] = message[-2]
    cities_lst.remove(message)
    used_cities_list.append(message)
    chosen_city = random.choice(cities_lst)
    while chosen_city[0] != context.user_data[LAST_LETTER]:
        chosen_city = random.choice(cities_lst)
    used_cities_list.append(chosen_city)
    cities_lst.remove(chosen_city)
    if chosen_city[-1] not in ['ь', 'ъ']:
        context.user_data[LAST_LETTER] = chosen_city[-1]
    else:
        context.user_data[LAST_LETTER] = message[-2]
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
    await update.message.reply_text('Откуда вы хотите получить изображение?', reply_markup=images_purgat_markup)
    return 'purgat'


async def return_images(update, context):
    command = update.message.text
    await update.message.reply_text('Рисую картинку! Это не займет много времени')
    print(command)
    output = replicate.run(
        "ai-forever/kandinsky-2:601eea49d49003e6ea75a11527209c4f510a93e2112c969d548fbb45b9c4f19f",
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
        await update.message.reply_text('По какому принципу вы хотите получить изображения?',
                                        reply_markup=top_images_markup)
        context.user_data[NUMBER_LINK] = 0
        return 'sorting'
    elif update.message.text == 'сгенерировать':
        await update.message.reply_text(
            'Что хотите видеть на картинке? Введите точный запрос на английском языке',
            reply_markup=ReplyKeyboardMarkup([exit]))
        return 'generate'
    else:
        await update.message.reply_text('Я не знаю такую команду')
        return 'purgat'


async def images_sort_message(update: Update, context):
    command = update.message.text
    if 'топ' in command:
        context.user_data[IS_RANDOM] = False
        count_top = int(command[command.find('топ') + 3:].strip())
        context.user_data[MAX_COUNT_LINK] = count_top - 1
        links = get_links(count_top)
        context.user_data[LINKS] = links
    elif command == 'рандомно':
        context.user_data[IS_RANDOM] = True
        context.user_data[NUMBER_LINK] = -1
        context.user_data[MAX_COUNT_LINK] = -1
        links = get_links(command)
        print('links', links)
        context.user_data[LINKS] = links
    else:
        context.user_data[IS_RANDOM] = False
        await update.message.reply_text('Я не знаю такую команду')
        return 'sorting'

    scrolling_images_markup = InlineKeyboardMarkup(creating_scrolling_markup(context))

    print(scrolling_images_lst)
    print(scrolling_images_markup)

    await bot.send_photo(update.message.chat.id, photo=open(links[context.user_data[NUMBER_LINK]], 'rb'),
                         reply_markup=scrolling_images_markup)
    context.user_data[MESSAGE_ID] = update.inline_query
    return 'scrolling'


def creating_scrolling_markup(context):
    links = context.user_data[LINKS]
    kb_lst = [[InlineKeyboardButton('👍', callback_data='like'),
               InlineKeyboardButton('likes...', callback_data='like'),
               InlineKeyboardButton('👎', callback_data='dislike')], [
                  InlineKeyboardButton('◀', callback_data='back'),
                  InlineKeyboardButton('...', callback_data='...'),
                  InlineKeyboardButton('▶', callback_data='forward')],
              [InlineKeyboardButton('name', callback_data='name')]]
    if context.user_data[IS_RANDOM]:
        del kb_lst[1][1]
    else:
        kb_lst[1][1] = InlineKeyboardButton(context.user_data[NUMBER_LINK] + 1, callback_data='page')
    kb_lst[2][0] = InlineKeyboardButton(
        str(db_sess.query(Image.key_word).filter(Image.link == str(links[context.user_data[NUMBER_LINK]]))[0][
                0]).capitalize(), callback_data='name')
    kb_lst[0][1] = InlineKeyboardButton(
        str(db_sess.query(Image.rating).filter(Image.link == str(links[context.user_data[NUMBER_LINK]]))[0][
                0]) + '❤',
        callback_data='likes')
    return kb_lst


async def scrolling_images(update: Update, context):
    query = update.callback_query
    print('query', query)
    recently = False
    if query.data == 'like':
        db_sess.query(Image).filter(Image.link == str(context.user_data[LINKS][-1])).first().rating += 1
        db_sess.commit()
    elif query.data == 'dislike':
        db_sess.query(Image).filter(Image.link == str(context.user_data[LINKS][-1])).first().rating -= 1
        db_sess.commit()
    elif query.data == 'back' and context.user_data[NUMBER_LINK] > 0:
        context.user_data[NUMBER_LINK] -= 1
    elif query.data == 'forward' and context.user_data[NUMBER_LINK] != context.user_data[MAX_COUNT_LINK]:
        context.user_data[NUMBER_LINK] += 1
        recently = True

    if context.user_data[IS_RANDOM] and query.data == 'forward' and context.user_data[NUMBER_LINK] == context.user_data[
        MAX_COUNT_LINK] and not recently:
        max_images = max(db_sess.query(Image.id))[0]
        id_image = random.randint(0, int(max_images) - 1)
        print(db_sess.query(Image.link)[id_image])
        link = db_sess.query(Image.link)[id_image][0]
        while link == context.user_data[LINKS][-1]:
            id_image = random.randint(0, int(max_images) - 1)
            link = db_sess.query(Image.link)[id_image][0]
        context.user_data[LINKS].append(link)
    elif query.data == 'back' and context.user_data[IS_RANDOM] and abs(context.user_data[NUMBER_LINK]) != len(
            context.user_data[LINKS]):
        context.user_data[NUMBER_LINK] -= 1
        link = context.user_data[LINKS][context.user_data[NUMBER_LINK]]
    else:
        link = context.user_data[LINKS][context.user_data[NUMBER_LINK]]

    scrolling_images_markup = InlineKeyboardMarkup(creating_scrolling_markup(context))

    media = telegram.InputMediaPhoto(media=open(link, 'rb'))

    print(context.user_data[NUMBER_LINK])
    await query.message.edit_media(media=media, reply_markup=scrolling_images_markup)


def get_links(command):
    links = []
    sorted_links = db_sess.query(Image.link).order_by(Image.rating.desc())
    if type(command) == int:
        for i in range(command):
            links.append(sorted_links[i][0])
    if command == 'рандомно':
        max_images = max(db_sess.query(Image.id))[0]
        print(max_images)
        id_image = random.randint(0, int(max_images) - 1)
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
    await update.message.reply_text("До встречи в чате!", reply_markup=ReplyKeyboardMarkup([['/start']]))


async def start_games(update, context):
    await update.message.reply_text('Давай поиграем! Выбери игру, в которую хочешь сыграть.', reply_markup=games_markup)
    return 'purgatory'


async def talking(update, context):
    await update.message.reply_text('С радостью пообщаюсь с тобой!', reply_markup=talk_markup)
    return 'continue'


async def start(update, context):
    await update.message.reply_text('Привет! Чем займемся сегодня?', reply_markup=quit_markup)
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
