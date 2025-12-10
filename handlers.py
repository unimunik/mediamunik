import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

# Глобальные переменные (для связи сообщений)
REPLY_MAPPING = {}

# Состояния FSM
class UserState(StatesGroup):
    waiting_for_message = State()
    anon_mode = State()
    open_mode = State()

# ---------------------------
#           КЛАВИАТУРЫ
# ---------------------------
def get_main_keyboard():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="🔒 Анонимное сообщение"),
        types.KeyboardButton(text="📨 Открытое сообщение")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

# ---------------------------
#        ОБРАБОТЧИКИ
# ---------------------------
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        "👋 Здравствуйте! Выберите тип сообщения:",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await message.answer(
        "✅ Действие отменено.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "🔒 Анонимное сообщение")
async def anon_mode_selected(message: types.Message, state: FSMContext):
    """Выбран анонимный режим"""
    user_id = message.from_user.id
    
    # Проверка подписки на канал
    try:
        member = await message.bot.get_chat_member(config.CHANNEL_ID, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await message.answer(
                f"⛔ Чтобы отправить анонимное сообщение, подпишитесь на канал:\n"
                f"<a href='{config.CHANNEL_LINK}'>ссылка</a>",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            return
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        await message.answer(
            "⚠️ Ошибка проверки подписки. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.set_state(UserState.waiting_for_message)
    await state.update_data(mode="anon")
    await message.answer(
        "✏️ Напишите ваше анонимное сообщение:\n"
        "(или отправьте фото/видео/голосовое)\n\n"
        "❌ Для отмены нажмите кнопку ниже.",
        reply_markup=get_cancel_keyboard()
    )

@router.message(F.text == "📨 Открытое сообщение")
async def open_mode_selected(message: types.Message, state: FSMContext):
    """Выбран открытый режим"""
    # Проверка username
    if not message.from_user.username:
        await message.answer(
            "❗ Для отправки открытых сообщений необходим username.\n"
            "Установите его в настройках Telegram и попробуйте снова.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.set_state(UserState.waiting_for_message)
    await state.update_data(mode="open")
    await message.answer(
        "✏️ Напишите ваше открытое сообщение:\n"
        "(или отправьте фото/видео/голосовое)\n\n"
        "❌ Для отмены нажмите кнопку ниже.",
        reply_markup=get_cancel_keyboard()
    )

@router.message(UserState.waiting_for_message)
async def process_user_message(message: types.Message, state: FSMContext):
    """Обработка сообщения от пользователя"""
    user_data = await state.get_data()
    mode = user_data.get("mode")
    
    if not mode:
        await message.answer("Ошибка. Начните заново.", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    # Определяем префикс в зависимости от режима
    if mode == "anon":
        prefix = "🔒 Анонимное сообщение"
        user_response = "✅ Сообщение отправлено анонимно!"
    else:  # open mode
        username = message.from_user.username or "Без username"
        prefix = f"📨 Открытое сообщение от @{username}"
        user_response = "✅ Ваше открытое сообщение отправлено!"
    
    # Отправляем сообщение владельцу
    sent_message = await forward_to_owner(message, prefix)
    
    # Сохраняем связь для ответа
    REPLY_MAPPING[sent_message.message_id] = message.from_user.id
    
    # Отвечаем пользователю
    await message.answer(user_response, reply_markup=get_main_keyboard())
    await state.clear()

@router.message(F.from_user.id == config.OWNER_ID, F.reply_to_message)
async def handle_owner_reply(message: types.Message):
    """Обработка ответа владельца через реплай"""
    replied_msg_id = message.reply_to_message.message_id
    
    if replied_msg_id not in REPLY_MAPPING:
        await message.reply("⚠️ Не удалось найти отправителя оригинального сообщения.")
        return
    
    target_user_id = REPLY_MAPPING[replied_msg_id]
    
    try:
        # Пересылаем ответ пользователю
        if message.text:
            await message.bot.send_message(
                target_user_id, 
                f"💬 Ответ от владельца:\n\n{message.text}"
            )
        elif message.photo:
            await message.bot.send_photo(
                target_user_id,
                message.photo[-1].file_id,
                caption=f"💬 Ответ от владельца"
            )
        elif message.video:
            await message.bot.send_video(
                target_user_id,
                message.video.file_id,
                caption=f"💬 Ответ от владельца"
            )
        elif message.voice:
            await message.bot.send_voice(
                target_user_id,
                message.voice.file_id,
                caption=f"💬 Ответ от владельца"
            )
        elif message.document:
            await message.bot.send_document(
                target_user_id,
                message.document.file_id,
                caption=f"💬 Ответ от владельца"
            )
        elif message.sticker:
            await message.bot.send_sticker(target_user_id, message.sticker.file_id)
        else:
            await message.bot.send_message(target_user_id, "💬 Ответ от владельца (медиа)")
        
        await message.reply("✅ Ответ отправлен пользователю!")
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")
        await message.reply(f"❌ Ошибка отправки: {e}")

@router.message()
async def handle_other_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    if message.from_user.id == config.OWNER_ID:
        # Владелец может отправлять команды
        return
    
    # Обычному пользователю показываем меню
    await message.answer(
        "👋 Выберите тип сообщения:",
        reply_markup=get_main_keyboard()
    )

# ---------------------------
#      ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ---------------------------
async def forward_to_owner(message: types.Message, prefix: str) -> types.Message:
    """Отправляет сообщение владельцу"""
    if message.text:
        return await message.bot.send_message(
            config.OWNER_ID, 
            f"{prefix}:\n\n{message.text}"
        )
    
    elif message.photo:
        return await message.bot.send_photo(
            config.OWNER_ID,
            message.photo[-1].file_id,
            caption=prefix
        )
    
    elif message.video:
        return await message.bot.send_video(
            config.OWNER_ID,
            message.video.file_id,
            caption=prefix
        )
    
    elif message.voice:
        return await message.bot.send_voice(
            config.OWNER_ID,
            message.voice.file_id,
            caption=prefix
        )
    
    elif message.document:
        return await message.bot.send_document(
            config.OWNER_ID,
            message.document.file_id,
            caption=prefix
        )
    
    elif message.sticker:
        return await message.bot.send_sticker(
            config.OWNER_ID,
            message.sticker.file_id
        )
    
    else:
        return await message.bot.send_message(
            config.OWNER_ID,
            f"{prefix}\n\n[Неподдерживаемый тип медиа]"
        )
