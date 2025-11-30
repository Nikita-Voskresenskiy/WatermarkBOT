# main.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
from middleware import AlbumMiddleware
from env_settings import env


async def main():
    bot = Bot(token=env.BOT_TOKEN)
    dp = Dispatcher()
    print("here")
    # Include router
    dp.include_router(router)

    # Add middleware
    dp.message.middleware(AlbumMiddleware())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
