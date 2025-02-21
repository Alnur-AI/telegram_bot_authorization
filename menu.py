from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router
from aiogram import Bot, Dispatcher

from auth import exit_handler

import config
bot = Bot(token=config.TOKEN)
dp = Dispatcher()
menu_router = Router()

@menu_router.callback_query(lambda c: c.data.startswith("open_shop"))
async def open_shop(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"🛒 Открываем магазин для Telegram ID: {telegram_id}")  # Логируем

    #await shop_handler(callback.message,telegram_id)
    await callback.answer()


@menu_router.callback_query(lambda c: c.data.startswith("open_inventory"))
async def open_inventory(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"🎒 Открываем инвентарь для Telegram ID: {telegram_id}")  # Логируем

    #await inventory_handler(callback.message)
    await callback.answer()


@menu_router.callback_query(lambda c: c.data.startswith("open_stats"))
async def open_stats(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"📊 Открываем статистику для Telegram ID: {telegram_id}")  # Логируем

    #await stat_handler(callback.message)
    await callback.answer()


@menu_router.callback_query(lambda c: c.data.startswith("logout"))
async def logout(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"🚪 Выход пользователя Telegram ID: {telegram_id}")  # Логируем

    await exit_handler(callback.message, telegram_id)
    await callback.answer()


@menu_router.callback_query(lambda c: c.data.startswith("find_game"))
async def find_game(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"🔍 Поиск игры для Telegram ID: {telegram_id}")  # Логируем

    await callback.answer("🔍 Найти игру - функция в разработке!")


@menu_router.callback_query(lambda c: c.data.startswith("interspace_training"))
async def interspace_training(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    print(f"🛰 Интерспейс тренировка для Telegram ID: {telegram_id}")  # Логируем

    await callback.answer("🛰 Интерспейс тренировка - функция в разработке!")


@menu_router.callback_query(lambda c: c.data.startswith("return_main_menu"))
async def return_to_main_menu(callback: CallbackQuery):
    data = callback.data.split("|")
    telegram_id = int(data[1]) if len(data) > 1 else None

    if telegram_id is None:
        await callback.answer("❌ Ошибка: Telegram ID не найден!", show_alert=True)
        return

    print(f"🔙 Возвращаем пользователя {telegram_id} в главное меню")

    try:
        await update_main_menu(callback.message.chat.id, callback.message.message_id, telegram_id)
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка при возврате в главное меню: {e}")


# ✅ Функция для редактирования сообщения после логина
async def update_main_menu(chat_id: int, message_id: int, telegram_id):
    if not chat_id or not message_id:
        print("❌ Ошибка: `chat_id` или `message_id` не переданы!")
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🎮 Главное меню:",
            reply_markup=get_main_inline_menu(telegram_id)
        )
    except Exception as e:
        print(f"❌ Ошибка при редактировании меню: {e}")


# 🔹 Функция для создания меню после входа
def get_main_inline_menu(telegram_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти игру", callback_data=f"find_game|{telegram_id}")],
            [InlineKeyboardButton(text="🛰 Интерспейс тренировка", callback_data=f"interspace_training|{telegram_id}")],
            [InlineKeyboardButton(text="🛒 Магазин", callback_data=f"open_shop|{telegram_id}"),
             InlineKeyboardButton(text="🎒 Инвентарь", callback_data=f"open_inventory|{telegram_id}")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"open_stats|{telegram_id}"),
             InlineKeyboardButton(text="🚪 Выйти", callback_data=f"logout|{telegram_id}")]
        ]
    )
