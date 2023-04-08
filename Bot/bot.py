import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

openai.api_key = "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"
token = '6217430570:AAE2I1NZYFIUjzYFCXZtYyTHi31rSR79RDE'

bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler()
async def send(message: types.Message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message.text,
        temperature=0.9,
        max_tokens=1000,
        top_p=0.7,
        frequency_penalty=0.0
    )
    await message.answer(response['choices'][0]['text'])


if __name__ == '__main__':
    executor.start_polling(dp)
