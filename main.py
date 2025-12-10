import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, OWNER_ID, CHANNEL_ID  # ← ИМПОРТИРУЕМ ВСЕ НУЖНЫЕ ПЕРЕМЕННЫЕ!

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Создаем бота
        bot = Bot(token=TOKEN)
        
        # Создаем диспетчер с хранилищем состояний
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Импортируем и подключаем роутер
        from handlers import router
        dp.include_router(router)
        
        logger.info("🤖 Бот запущен и готов к работе!")
        logger.info(f"📞 Владелец: {OWNER_ID}")  # ← Теперь OWNER_ID доступен
        logger.info(f"📢 Канал ID: {CHANNEL_ID}")
        
        # Запускаем
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
