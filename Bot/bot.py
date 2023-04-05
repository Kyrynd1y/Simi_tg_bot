import json
import logging
from telegram.ext import MessageHandler, CommandHandler, Application, filters
import apiai

BOT_TOKEN = '6217430570:AAE2I1NZYFIUjzYFCXZtYyTHi31rSR79RDE'
project_id = 'simi-ukah'


def startCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Привет, давай пообщаемся?')


def textMessage(bot, update):
    request = apiai.ApiAI(project_id).text_request()  # Токен API к Dialogflow
    request.lang = 'ru'  # На каком языке будет послан запрос
    request.session_id = 'BatlabAIBot'  # ID Сессии диалога (нужно, чтобы потом учить бота)
    request.query = update.message.text  # Посылаем запрос к ИИ с сообщением от юзера
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech']  # Разбираем JSON и вытаскиваем ответ
    # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
    if response:
        bot.send_message(chat_id=update.message.chat_id, text=response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Я Вас не совсем понял!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', startCommand))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, textMessage()))
    application.run_polling()


if __name__ == '__main__':
    main()
