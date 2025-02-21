import aiosqlite
from aiogram import Bot

import config
bot = Bot(token=config.TOKEN)
DB_PATH = config.DB_PATH

from db_functions import notify_all_users

async def deactivate_all_sessions():
    """Деактивирует все активные сессии в user_session_history."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
                UPDATE user_session_history
                SET is_active = FALSE, was_notified = TRUE
                WHERE is_active = TRUE
            """)
        await db.commit()
async def shutdown():
    """Действия при завершении бота."""
    print("❌ Бот выключается...")
    await notify_all_users("❌ Сервер завершил свою работу! Все сессии более не активны!")
    await deactivate_all_sessions()
    await bot.session.close()  # Закрываем соединение с ботом

