import asyncio
import aiosqlite
from aiogram import Router
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from argon2 import PasswordHasher

import config
bot = Bot(token=config.TOKEN)
DB_PATH = config.DB_PATH
dp = Dispatcher()
ph = PasswordHasher()

auth_router = Router()

class Registration(StatesGroup):
    credentials = State()  # Ожидаем "логин пароль"


class Login(StatesGroup):
    credentials = State()  # Ожидаем "логин пароль"


# ✅ Создаем кастомное событие
async def event_update_main_menu(chat_id, message_id, telegram_id):
    """Запускаем обновление главного меню после логина"""
    from menu import update_main_menu  # ✅ Импортируем внутри функции, чтобы избежать циклического импорта
    await update_main_menu(chat_id, message_id, telegram_id)  # ✅ Вызываем `update_main_menu` с параметрами

# Обработчик команды /start
@auth_router.message(Command("start"))
async def start_handler(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT security.user_id, users.user_name 
               FROM security 
               JOIN users ON security.user_id = users.user_id
               WHERE security.telegram_id = ?""",
            (message.from_user.id,)
        ) as cursor:
            accounts = await cursor.fetchall()

    if accounts:
        # Формируем список существующих аккаунтов
        accounts_list = "\n".join([f"{acc[1]} (ID: {acc[0]})" for acc in accounts])
        await message.answer(
            f"Вы уже зарегистрированы с {len(accounts)} аккаунтом(ами):\n\n{accounts_list}\n\n"
            "Вы можете войти в один из существующих аккаунтов с помощью /login "
            "или зарегистрировать новый аккаунт с /reg."
        )
    else:
        await message.answer("Вы не зарегистрированы. Введите /reg для регистрации.")

# /reg
@auth_router.message(Command("reg"))
async def reg_handler(message: Message, state: FSMContext):
    await state.set_state(Registration.credentials)
    await message.answer("Введите имя пользователя и пароль через пробел:")
@auth_router.message(Registration.credentials)
async def reg_credentials_handler(message: Message, state: FSMContext):
    credentials = message.text.strip().split(" ", 1)

    if len(credentials) != 2:
        await message.answer("Некорректный формат! Введите имя пользователя и пароль через пробел.")
        return

    username, password = credentials
    hashed_password = ph.hash(password)

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, существует ли уже такой username
        async with db.execute("SELECT user_id FROM users WHERE user_name = ?", (username,)) as cursor:
            existing = await cursor.fetchone()
        if existing:
            await message.answer("Такое имя уже занято! Введите другое:")
            return

        # Создаём новый user_id (берём максимум + 1)
        async with db.execute("SELECT MAX(user_id) FROM users") as cursor:
            max_id = await cursor.fetchone()
            new_user_id = (max_id[0] or 0) + 1

        # Создаём пустой инвентарь для пользователя
        await db.execute("INSERT INTO inventory (user_id, items) VALUES (?, ?)",
                         (new_user_id, '{}'))

        # Сохраняем пользователя в security (telegram_id уникален, но user_id может быть разным)
        await db.execute("INSERT INTO security (telegram_id, user_id, password) VALUES (?, ?, ?)",
                         (message.from_user.id, new_user_id, hashed_password))

        # Добавляем пользователя в таблицу users
        await db.execute("INSERT INTO users (telegram_id, user_id, user_name, reg_date) VALUES (?, ?, ?, ?)",
                         (message.from_user.id, new_user_id, username, datetime.now()))

        await db.commit()

    await state.clear()
    await message.answer(f"Регистрация успешна! Ваш логин: {username}. Теперь введите /login.")

# /login
@auth_router.message(Command("login"))
async def login_handler(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM security WHERE telegram_id = ?", (message.from_user.id,)) as cursor:
            user = await cursor.fetchone()

        if not user:
            await message.answer("Вы не зарегистрированы! Введите /reg.")
            return

        user_id = user[0]
        async with db.execute("SELECT is_active FROM user_session_history WHERE user_id = ? AND is_active = TRUE",
                              (user_id,)) as cursor:
            active_session = await cursor.fetchone()

        if active_session:
            await message.answer("У вас уже есть активная сессия!")
            return

    await state.set_state(Login.credentials)
    await message.answer("Введите логин и пароль через пробел:")
@auth_router.message(Login.credentials)
async def login_credentials_handler(message: Message, state: FSMContext):
    try:
        username, password = message.text.strip().split(maxsplit=1)
    except ValueError:
        await message.answer("Некорректный формат! Введите логин и пароль через пробел:")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, password FROM security WHERE user_id = (SELECT user_id FROM users WHERE user_name = ?)",
                              (username,)) as cursor:
            user = await cursor.fetchone()
        if not user:
            await message.answer("Пользователь не найден! Попробуйте снова.")
            return

    user_id, stored_hash = user

    try:
        ph.verify(stored_hash, password)
    except Exception:
        await message.answer("Неверный пароль! Попробуйте снова.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            login_time = datetime.now()

            # Вставляем новую сессию
            await db.execute(
                "INSERT INTO user_session_history (user_id, login_time, is_active, last_activity) VALUES (?, ?, ?, ?)",
                (user_id, login_time, True, login_time)
            )

            # Получаем log_id только что созданной сессии
            async with db.execute(
                    "SELECT log_id FROM user_session_history WHERE user_id = ? ORDER BY log_id DESC LIMIT 1",
                    (user_id,)
            ) as cursor:
                last_log_id = await cursor.fetchone()

            if last_log_id:
                # Обновляем last_log_id в security
                await db.execute(
                    "UPDATE security SET last_log_id = ? WHERE user_id = ?",
                    (last_log_id[0], user_id)
                )
                # ✅ Отправляем временное сообщение
                sent_message = await message.answer("✅ Вы успешно вошли!")

                # 🔥 Отправляем кастомное событие через `asyncio.create_task()`
                telegram_id = message.from_user.id
                asyncio.create_task(event_update_main_menu(message.chat.id, sent_message.message_id, telegram_id))
            else:
                await message.answer("Ошибка: не удалось получить log_id новой сессии!")

            await db.commit()
            await state.clear()

        except Exception as e:
            await message.answer(f"Ошибка при обработке сессии: {str(e)}")
            await db.rollback()

# /exit
# Функция для завершения текущей сессии
async def exit_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Завершаем активную сессию
        await db.execute("""
            UPDATE user_session_history 
            SET is_active = FALSE, was_notified = TRUE
            WHERE user_id = ? AND is_active = TRUE
        """, (user_id,))
        await db.commit()

@auth_router.message(Command("exit"))
async def exit_handler(message: Message, telegram_id):

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем user_id по telegram_id
        async with db.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            result = await cursor.fetchone()

        if not result:
            await message.answer("Вы не зарегистрированы в системе.")
            return

        user_id = result[0]

        # Проверяем, есть ли активная сессия
        async with db.execute("""
            SELECT COUNT(*) FROM user_session_history 
            WHERE user_id = ? AND is_active = TRUE
        """, (user_id,)) as cursor:
            active_sessions = await cursor.fetchone()

        if active_sessions[0] == 0:
            await message.answer("У вас нет активной сессии.")
            return

        # Завершаем сессию
        await exit_session(user_id)
        await message.answer("Вы успешно вышли из системы. Ваша сессия завершена.")


