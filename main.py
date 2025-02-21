# LIBRARIES
import asyncio

# MODULES
import config

from menu import menu_router
from auth import auth_router

from init import init_db,reset_sessions,startup
from db_functions import check_sessions
from shutdown import shutdown

# PARAMETERS
bot = config.bot
DB_PATH = config.DB_PATH

# ROUTERS
dp = config.dp
ph = config.ph

dp.include_router(menu_router)
dp.include_router(auth_router)


async def main():

    """Основная функция, запускающая бота и обрабатывающая сигналы завершения."""
    await init_db()
    await startup()
    await reset_sessions()

    # Запускаем проверку неактивных сессий
    asyncio.create_task(check_sessions())

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен пользователем.")
    finally:
        await shutdown()

if __name__ == "__main__":
    asyncio.run(main())