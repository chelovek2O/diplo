import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from db import init_db, delete_old_posts
from handlers import dp

async def main():
    init_db()
    delete_old_posts()
    bot = Bot(token=TOKEN)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(dp)
    print("Бот запущен")
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())