from argon2 import PasswordHasher
from aiogram import Dispatcher
from aiogram import Bot

TOKEN = "PUT YOUR TOKEN HERE"
DB_PATH = "users.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()
ph = PasswordHasher()

MODULES = ['']