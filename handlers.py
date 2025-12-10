from aiogram import types
import config
import logging

logging.basicConfig(level=logging.ERROR)

REPLY_MAPPING = {}
USER_MODE = {}  # NEW: {user_id: "anon" or "open"}

# --- NEW: главное меню ---
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔒 Анонимное сообщение", "📨 Открытое сообщение")
    return kb


# ---------------------------
#        /start handler
# ---------------------------
async def start_handler(message: types.Message):
    await message.answer(
        "Здравствуйте! Выберите тип сообщения:",
        reply_markup=main_menu()
    )


# ---------------------------
#    message_handler
# ---------------------------
async def message_handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    # ============================================
    #                 ВЫБОР РЕЖИМА
    # ============================================

    # --- Анонимный режим ---
    if text == "🔒 Анонимное сообщение":
        # Проверка подписки
        try:
            member = await message.bot.get_chat_member(config.CHANNEL_ID, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await message.answer(
                    f"⛔ Чтобы отправить анонимное сообщение, подпишитесь на канал:\n"
                    f"<a href='{config.CHANNEL_LINK}'>ссылка</a>",
                    parse_mode="HTML"
                )
                return
        except Exception:
            await message.answer("Ошибка проверки подписки.")
            return

        USER_MODE[user_id] = "anon"
        await message.answer("✏️ Напишите ваше анонимное сообщение:")
        return


    # --- Открытый режим ---
    if text == "📨 Открытое сообщение":
        # Проверка username
        if not message.from_user.username:
            await message.answer(
                "❗ Вы не можете отправить открытое сообщение без установленного username.\n"
                "Установите username в настройках Telegram и попробуйте снова."
            )
            return

        USER_MODE[user_id] = "open"
        await message.answer("✏️ Напишите ваше открытое сообщение:")
        return


    # ============================================
    #      ОТВЕТ ВЛАДЕЛЬЦА ЧЕРЕЗ РЕPLY
    # ============================================
    if user_id == config.OWNER_ID and message.reply_to_message:
        replied_msg_id = message.reply_to_message.message_id

        if replied_msg_id in REPLY_MAPPING:
            target_user = REPLY_MAPPING[replied_msg_id]

            # Отправка медиа/текста
            if message.text:
                await message.bot.send_message(target_user, f"Ответ от владельца:\n{message.text}")
            elif message.photo:
                await message.bot.send_photo(target_user, message.photo[-1].file_id)
            elif message.video:
                await message.bot.send_video(target_user, message.video.file_id)
            elif message.voice:
                await message.bot.send_voice(target_user, message.voice.file_id)
            elif message.document:
                await message.bot.send_document(target_user, message.document.file_id)
            elif message.sticker:
                await message.bot.send_sticker(target_user, message.sticker.file_id)
            else:
                await message.bot.send_message(target_user, "Ответ от владельца (медиа)")

            await message.reply("Отправлено!")
            return

    # ============================================
    #              ОТПРАВКА СООБЩЕНИЙ
    # ============================================
    mode = USER_MODE.get(user_id)

    # --- Если человек НЕ выбрал режим ---
    if not mode:
        await message.answer("Выберите тип сообщения:", reply_markup=main_menu())
        return

    # --- Анонимный режим ---
    if mode == "anon":
        sent = await forward_message_to_owner(message, prefix="Анонимное сообщение")
        REPLY_MAPPING[sent.message_id] = user_id
        await message.answer("Отправлено анонимно!")
        return

    # --- Открытый режим ---
    if mode == "open":
        username = message.from_user.username

        sent = await forward_message_to_owner(
            message,
            prefix=f"Открытое сообщение от @{username}"
        )

        REPLY_MAPPING[sent.message_id] = user_id
        await message.answer("Ваше открытое сообщение отправлено!")
        return


# ---------------------------
#  Функция отправки владельцу
# ---------------------------
async def forward_message_to_owner(message: types.Message, prefix=""):
    """Отправляет любые медиа владельцу + текст"""
    bot = message.bot

    if message.text:
        return await bot.send_message(config.OWNER_ID, f"{prefix}:\n{message.text}")

    if message.photo:
        return await bot.send_photo(config.OWNER_ID, message.photo[-1].file_id, caption=prefix)

    if message.video:
        return await bot.send_video(config.OWNER_ID, message.video.file_id, caption=prefix)

    if message.voice:
        return await bot.send_voice(config.OWNER_ID, message.voice.file_id, caption=prefix)

    if message.document:
        return await bot.send_document(config.OWNER_ID, message.document.file_id, caption=prefix)

    if message.sticker:
        return await bot.send_sticker(config.OWNER_ID, message.sticker.file_id)

    return await bot.send_message(config.OWNER_ID, f"{prefix}\n(неподдерживаемый тип)")
