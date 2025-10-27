# handlers.py
from aiogram import types
import config  # Импортируем конфиг для доступа к ID и ссылке
import logging  # Добавили для логов

# Настраиваем логи (вывод в консоль)
logging.basicConfig(level=logging.ERROR)

REPLY_MAPPING = {}  # Глобальный dict для хранения {message_id_у_владельца: user_id_отправителя}

async def start_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await message.bot.get_chat_member(config.CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await message.reply("Вы подписаны! Отправьте мне сообщение, и я анонимно передам его владельцу.")
        else:
            await message.reply(
                f"⛔️ Чтобы пользоваться ботом, подпишись на приватный канал по <a href='{config.CHANNEL_LINK}'>ссылке</a>\nПосле подписки попробуйте отправить сообщение снова.",
                parse_mode='HTML'
            )
    except Exception as e:
        if 'user not found' in str(e).lower():
            await message.reply(
                f"⛔️ Чтобы пользоваться ботом, подпишись на приватный канал по <a href='{config.CHANNEL_LINK}'>ссылке</a>\nПосле подписки попробуйте отправить сообщение снова.",
                parse_mode='HTML'
            )
        else:
            logging.error(f"Ошибка в start_handler: {str(e)}")  # Лог в консоль
            await message.reply("Ошибка проверки. Попробуйте позже.")

async def message_handler(message: types.Message):
    user_id = message.from_user.id

    # Если сообщение от владельца и это reply
    if user_id == config.OWNER_ID and message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id
        if replied_msg_id in REPLY_MAPPING:
            target_user_id = REPLY_MAPPING[replied_msg_id]
            # Отправляем ответ пользователю (текст или медиа)
            if message.text:
                await message.bot.send_message(target_user_id, f"Ответ от владельца: {message.text}")
            elif message.photo:
                await message.bot.send_photo(target_user_id, message.photo[-1].file_id, caption="Ответ от владельца (фото)")
            elif message.video:
                await message.bot.send_video(target_user_id, message.video.file_id, caption="Ответ от владельца (видео)")
            elif message.audio:
                await message.bot.send_audio(target_user_id, message.audio.file_id, caption="Ответ от владельца (аудио)")
            elif message.voice:
                await message.bot.send_voice(target_user_id, message.voice.file_id, caption="Ответ от владельца (голосовое)")
            elif message.video_note:
                await message.bot.send_video_note(target_user_id, message.video_note.file_id)
            elif message.document:
                await message.bot.send_document(target_user_id, message.document.file_id, caption="Ответ от владельца (файл)")
            elif message.sticker:
                await message.bot.send_sticker(target_user_id, message.sticker.file_id)  # Без caption
            else:
                await message.bot.send_message(target_user_id, f"Ответ от владельца: {message.text or 'Медиа без текста'}")
            await message.reply("Ответ отправлен пользователю!")
            return  # Выходим, чтобы не обрабатывать как анонимное

    # Проверка подписки для обычных пользователей
    try:
        member = await message.bot.get_chat_member(config.CHANNEL_ID, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await message.reply(
                f"⛔️ Чтобы пользоваться ботом, подпишись на приватный канал по <a href='{config.CHANNEL_LINK}'>ссылке</a>\nПосле подписки попробуйте отправить сообщение снова.",
                parse_mode='HTML'
            )
            return
    except Exception as e:
        logging.error(f"Ошибка в message_handler: {str(e)}")  # Лог в консоль
        await message.reply("Ошибка проверки. Попробуйте позже.")
        return

    # Анонимная отправка владельцу (текст или медиа)
    if message.text:
        sent_msg = await message.bot.send_message(config.OWNER_ID, f"Анонимное сообщение: {message.text}")
    elif message.photo:
        sent_msg = await message.bot.send_photo(config.OWNER_ID, message.photo[-1].file_id, caption="Анонимное фото")
    elif message.video:
        sent_msg = await message.bot.send_video(config.OWNER_ID, message.video.file_id, caption="Анонимное видео")
    elif message.audio:
        sent_msg = await message.bot.send_audio(config.OWNER_ID, message.audio.file_id, caption="Анонимное аудио")
    elif message.voice:
        sent_msg = await message.bot.send_voice(config.OWNER_ID, message.voice.file_id, caption="Анонимное голосовое")
    elif message.video_note:
        sent_msg = await message.bot.send_video_note(config.OWNER_ID, message.video_note.file_id)
    elif message.document:
        sent_msg = await message.bot.send_document(config.OWNER_ID, message.document.file_id, caption="Анонимный файл")
    elif message.sticker:
        sent_msg = await message.bot.send_sticker(config.OWNER_ID, message.sticker.file_id)  # Без caption
    else:
        await message.reply("Тип сообщения не поддерживается.")
        return

    # Сохраняем mapping для ответа
    REPLY_MAPPING[sent_msg.message_id] = user_id
    await message.reply("Сообщение отправлено анонимно!")