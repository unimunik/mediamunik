# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers import router  # ← ИМПОРТИРУЕМ РОУТЕР!

dp = Dispatcher(storage=MemoryStorage())  # ← Добавляем storage
dp.include_router(router)  # ← Подключаем роутер

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
