# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram import types
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
from handlers import start_handler, message_handler

dp = Dispatcher()

# Регистрируем handlers
dp.message.register(start_handler, CommandStart())
dp.message.register(message_handler)  # Это поймает все сообщения, включая медиа

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':

    asyncio.run(main())
