from aiogram.types import Message, CallbackQuery, InlineQuery
from datetime import datetime
import aiosqlite
import logging
import asyncio, aiogram
from aiogram import Bot

import config
bot = Bot(token=config.TOKEN)
DB_PATH = config.DB_PATH

async def find_active_user_id(db, telegram_id):
    """Ищет активный user_id по telegram_id"""

    if telegram_id is None:
        print("❌ Ошибка: не удалось определить telegram_id!")
        return None

    print(f"🔍 Поиск user_id для telegram_id: {telegram_id}")

    async with db.execute("""
        SELECT u.user_id 
        FROM user_session_history ush
        JOIN users u ON ush.user_id = u.user_id
        WHERE u.telegram_id = ? AND ush.is_active = TRUE
        ORDER BY ush.last_activity DESC
        LIMIT 1
    """, (telegram_id,)) as cursor:
        result = await cursor.fetchone()

    if not result:
        print(f"⚠ Пользователь {telegram_id} не найден в активных сессиях!")
        return None

    user_id = result[0]
    print(f"✅ Найден user_id: {user_id} для telegram_id {telegram_id}")
    return user_id


async def update_last_activity(db, telegram_id: int):
    """Обновляет поле last_activity в user_session_history на текущее время."""

    user_id = await find_active_user_id(db, telegram_id)
    print(f"update_last_activity {user_id}")
    now = datetime.now()
    await db.execute("""
        UPDATE user_session_history 
        SET last_activity = ? 
        WHERE user_id = ? AND is_active = TRUE
    """, (now, user_id))
    await db.commit()



async def notify_all_users(message: str):
    """Отправляет сообщение всем зарегистрированным пользователям."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT telegram_id "
                              "FROM security "
                              "WHERE telegram_id IS NOT NULL "
                              "GROUP BY telegram_id") as cursor:
            users = await cursor.fetchall()

    for (telegram_id,) in users:
        try:
            await bot.send_message(telegram_id, message)
        except Exception as e:
            print(f"Ошибка отправки пользователю {telegram_id}: {e}")
# Функция проверки всех сессий (переделать чтобы смотрела только активные)
async def check_sessions():
    max_session_time = 3600
    function_delay = 60

    while True:
        async with aiosqlite.connect(DB_PATH) as db:
            now = datetime.now()

            # Выбираем user_id, last_activity и was_notified только для активных сессий
            async with db.execute("""
                SELECT user_id, last_activity, was_notified 
                FROM user_session_history 
                WHERE is_active = TRUE
            """) as cursor:
                active_sessions = await cursor.fetchall()

            for user_id, last_activity, was_notified in active_sessions:
                try:
                    last_activity_time = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S.%f")

                    # Если прошло больше 10 секунд с момента последней активности
                    if (now - last_activity_time).total_seconds() > max_session_time:
                        # Деактивируем сессию по user_id
                        await db.execute("""
                            UPDATE user_session_history 
                            SET is_active = FALSE, was_notified = TRUE
                            WHERE user_id = ?
                        """, (user_id,))
                        await db.commit()

                        # Получаем telegram_id пользователя
                        async with db.execute("""
                            SELECT telegram_id FROM users WHERE user_id = ?
                        """, (user_id,)) as user_cursor:
                            user = await user_cursor.fetchone()

                        if user and not was_notified:
                            telegram_id = user[0]
                            try:
                                await bot.send_message(telegram_id, "Ваша сессия истекла. Пожалуйста, войдите снова с помощью /login")
                            except aiogram.exceptions.TelegramBadRequest as e:
                                logging.warning(f"Не удалось отправить сообщение пользователю {telegram_id}: {e}")

                except Exception as e:
                    logging.error(f"Ошибка при обработке пользователя {user_id}: {e}")

        await asyncio.sleep(function_delay)
