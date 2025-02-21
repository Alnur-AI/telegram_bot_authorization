from aiogram import Bot
import aiosqlite

import config
bot = Bot(token=config.TOKEN)
DB_PATH = config.DB_PATH

from db_functions import notify_all_users

async def startup():
    """Действия при запуске бота."""
    print("🔄 Бот запускается...")
    await notify_all_users("✅ Сервер возобновил свою работу, можете авторизироваться через /login")
# Функция для инициализации базы данных
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        
        CREATE TABLE IF NOT EXISTS gate_def (
            gt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price INTEGER,
            def TEXT,
            class INTEGER,
            type INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS bakugan_def (
            bakugan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            g_power INTEGER,
            price INTEGER,
            level INTEGER,
            max_attribute INTEGER
        );


        CREATE TABLE IF NOT EXISTS security (
            telegram_id INTEGER,
            user_id INTEGER PRIMARY KEY,
            password TEXT,
            last_log_id INTEGER,
            access_level INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS user_session_history (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER ,
            login_time DATETIME,
            is_active BOOLEAN DEFAULT TRUE,
            platform INTEGER DEFAULT 0,
            last_activity DATETIME,
            was_notified BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER,
            user_id INTEGER PRIMARY KEY,
            user_name TEXT UNIQUE,
            reg_date DATETIME,
            level INTEGER DEFAULT 0,
            hsp INTEGER DEFAULT 0,
            bakucoin INTEGER DEFAULT 1000
        );

        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER PRIMARY KEY,
            items JSON DEFAULT '{}'
        );
        """)
        await db.commit()
        print("База данных инициализирована")
# Функция для завершения всех активных сессий при старте
async def reset_sessions():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE user_session_history "
                         "SET is_active = FALSE, was_notified = TRUE "
                         "WHERE is_active = TRUE;")
        await db.commit()
        print("Все активные сессии отключены и помечены как уведомленные.")
