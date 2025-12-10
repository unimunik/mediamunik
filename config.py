# config.py

TOKEN = os.environ.get("BOT_TOKEN")

# Проверяем, что токен загружен
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")


CHANNEL_ID = -1001574986721    # ID приватного канала (int, aiogram принимает int или str, но int предпочтительнее)
OWNER_ID = 777685945           # Твой Telegram ID (int)

CHANNEL_LINK = 'https://t.me/+rf26Mmg3JDk0ZjEy'  # Ссылка на приватный канал (добавил, как в обновлении для сообщений о подписке)

