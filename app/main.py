import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import os
from pathlib import Path
from watermark_algorithm import apply_watermark
from typing import List, Dict, Any, Callable, Awaitable
import json
from aiogram import BaseMiddleware
from env_settings import env

# Bot setup
bot = Bot(token=env.BOT_TOKEN)
dp = Dispatcher()


# User states
class UserState:
    WAITING_FOR_PHOTOS = 1
    WAITING_FOR_TEXT = 2


# User data storage (in production use database)
user_data = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_user_data(user_id):
    """Initialize or reset user data with all required fields"""
    user_data[user_id] = {
        "state": UserState.WAITING_FOR_PHOTOS,
        "photos": [],  # This will store all photos/files from both handlers
        "watermarked_photos": [],
        "watermark_text": None,
    }

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=env.CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription for {user_id}: {e}")
        return False


def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Подписаться на канал",
        url=f"https://t.me/{env.CHANNEL_USERNAME}")  # Replace with your channel username
    )
    builder.add(InlineKeyboardButton(
        text="Проверить подписку",
        callback_data="check_subscription")
    )
    return builder.as_markup()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id

    if not await check_subscription(user_id):
        await message.answer(
            "Для использования бота необходимо подписаться на наш канал.",
            reply_markup=get_subscription_keyboard()
        )
        return

    init_user_data(user_id)

    await message.answer(
        "Пришлите мне одну или несколько фотографий или файлов в формате PNG, JPEG."
    )


def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="↪️ начать заново",
        callback_data="restart")
    )
    builder.add(InlineKeyboardButton(
        text="🔡 задать текст",
        callback_data="to_text")
    )
    return builder.as_markup()

def get_main_keyboard2():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="↪️ начать заново",
        callback_data="restart")
    )
    builder.add(InlineKeyboardButton(
        text="🔡 исправить текст",
        callback_data="to_text")
    )
    return builder.as_markup()


@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.answer("Вы подписаны на канал! Спасибо!", show_alert=True)
        await start_handler(callback.message)
    else:
        await callback.answer("Вы еще не подписаны на канал!", show_alert=True)


class AlbumMiddleware(BaseMiddleware):
    """Middleware to handle media groups (albums)"""
    album_data: Dict[str, List[types.Message]] = {}

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            message: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        if not message.media_group_id:
            return await handler(message, data)

        if message.media_group_id not in self.album_data:
            self.album_data[message.media_group_id] = []
            # Schedule album processing
            asyncio.create_task(self._process_album(handler, message.media_group_id, data))

        self.album_data[message.media_group_id].append(message)
        return

    async def _process_album(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            media_group_id: str,
            data: Dict[str, Any]
    ):
        await asyncio.sleep(1)  # Wait for all parts to arrive

        if media_group_id in self.album_data and self.album_data[media_group_id]:
            album_messages = self.album_data.pop(media_group_id)
            data["album"] = album_messages
            await handler(album_messages[0], data)  # Process with first message

@dp.message(F.media_group_id, F.content_type.in_({'photo', 'document'}))
async def handle_albums(message: types.Message, album: List[types.Message]):
    user_id = message.from_user.id

    # Check subscription first
    if not await check_subscription(user_id):
        await message.answer(
            "Please subscribe to our channel first.",
            reply_markup=get_subscription_keyboard()
        )
        return

    if user_id not in user_data or user_data[user_id]["state"] != UserState.WAITING_FOR_PHOTOS:
        await message.answer("Пожалуйста, начните с команды /start")
        return

    saved_files = 0
    user_dir = Path(f"files/{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)

    for msg in album:
        try:
            # Handle photos
            if msg.photo:
                file_id = msg.photo[-1].file_id  # Highest resolution
                file = await bot.get_file(file_id)
                file_path = file.file_path
                ext = os.path.splitext(file_path)[1] or ".jpg"
                dest = user_dir / f"photo_{len(user_data[user_id]['photos'])}{ext}"
                await bot.download_file(file_path, destination=dest)
                user_data[user_id]["photos"].append(str(dest))
                saved_files += 1

            # Handle document images
            elif msg.document and msg.document.mime_type.startswith('image/'):
                file_id = msg.document.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path
                filename = msg.document.file_name or f"doc_{len(user_data[user_id]['photos'])}{os.path.splitext(file_path)[1]}"
                dest = user_dir / filename
                await bot.download_file(file_path, destination=dest)
                user_data[user_id]["photos"].append(str(dest))
                saved_files += 1

        except Exception as e:
            logger.error(f"Error processing album file: {e}")

    await message.answer(
        f"Фото сохранено. Всего файлов: {len(user_data[user_id]['photos'])}\n\n"
        "Вы можете прислать еще фото. Чтобы перейти к заданию водяного знака, нажмите '🔡 задать текст'.",
        reply_markup=get_main_keyboard()
    )

    # Only send confirmation for the last message in album
    if message == album[-1] and saved_files > 0:
        await message.answer(
            f"Saved {saved_files} files from album\n"
            f"Total files: {len(user_data[user_id]['photos'])}",
            reply_markup=get_main_keyboard()
        )

@dp.message(F.photo | F.document)
async def handle_files(message: types.Message):
    # Skip if this is part of an album (will be handled by handle_albums)
    if message.media_group_id is not None:
        return

    user_id = message.from_user.id

    # Check subscription first
    if not await check_subscription(user_id):
        await message.answer(
            "Для продолжения необходимо подписаться на наш канал.",
            reply_markup=get_subscription_keyboard()
        )
        return

    if user_id not in user_data or user_data[user_id]["state"] != UserState.WAITING_FOR_PHOTOS:
        await message.answer("Пожалуйста, начните с команды /start")
        return

    # Skip if this is part of an album (will be handled by handle_albums)
    if message.media_group_id:
        return

    # Create user directory if it doesn't exist
    user_dir = Path(f"files/{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Handle single photo
        if message.photo:
            file_id = message.photo[-1].file_id  # Get highest resolution photo
            file = await bot.get_file(file_id)
            file_path = file.file_path
            ext = os.path.splitext(file_path)[1] or ".jpg"
            dest = user_dir / f"photo_{len(user_data[user_id]['photos'])}{ext}"
            await bot.download_file(file_path, destination=dest)
            user_data[user_id]["photos"].append(str(dest))
            await message.answer(
                f"Фото сохранено. Всего файлов: {len(user_data[user_id]['photos'])}\n\n"
                "Вы можете прислать еще фото. Чтобы перейти к заданию водяного знака, нажмите '🔡 задать текст'.",
                reply_markup=get_main_keyboard()
            )

        # Handle single document
        elif message.document:
            mime_type = message.document.mime_type
            if mime_type and mime_type.split('/')[0] == 'image':
                file_id = message.document.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path
                filename = message.document.file_name or f"doc_{len(user_data[user_id]['photos'])}{os.path.splitext(file_path)[1]}"
                dest = user_dir / filename
                await bot.download_file(file_path, destination=dest)
                user_data[user_id]["photos"].append(str(dest))
                await message.answer(
                    f"Документ сохранен. Всего файлов: {len(user_data[user_id]['photos'])}\n\n"
                    "Вы можете прислать еще файлы. Чтобы перейти к заданию водяного знака, нажмите '🔡 задать текст'.",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer("Неподдерживаемый формат файла. Пришлите изображение (JPEG, PNG).")

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await message.answer("Произошла ошибка при сохранении файла. Пожалуйста, попробуйте еще раз.")

@dp.callback_query(lambda c: c.data == "to_text")
async def to_text_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer("Пожалуйста, начните с команды /start", show_alert=True)
        return

    if len(user_data[user_id]["photos"]) == 0:
        await callback.answer("Сначала пришлите хотя бы одно фото", show_alert=True)
        return

    # Set state to wait for watermark text
    user_data[user_id]["state"] = UserState.WAITING_FOR_TEXT
    user_data[user_id]["watermark_text"] = None  # Initialize watermark text storage
    await callback.message.answer("Теперь введите текст для водяного знака:")


@dp.message(F.text)
async def handle_watermark_text(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id]["state"] != UserState.WAITING_FOR_TEXT:
        await message.answer("Сначала отправьте хотя бы одно фото. Если вы уже отправили фото, нажмите 'задать текст'")
        return

    # Store the watermark text
    watermark_text = message.text
    user_data[user_id]["watermark_text"] = watermark_text

    # Create output directory
    output_dir = Path(f"files/{user_id}/watermarked")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize storage for watermarked files if not exists
    if "watermarked_photos" not in user_data[user_id]:
        user_data[user_id]["watermarked_photos"] = []

    # Process each file with watermark and send to user
    processed_files = 0
    sent_files = 0

    for file_path in user_data[user_id]["photos"]:
        try:
            original_path = Path(file_path)
            output_filename = f"wm_{original_path.stem}{original_path.suffix}"
            output_path = output_dir / output_filename

            # Apply watermark
            success = apply_watermark(
                file_path=str(original_path),
                watermark_text=watermark_text,
                output_path=str(output_path)
            )

            if success:
                processed_files += 1
                # Store watermarked file path separately
                user_data[user_id]["watermarked_photos"].append(str(output_path))

                # Send watermarked file to user
                try:
                    if output_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        await message.answer_photo(
                            types.FSInputFile(output_path))
                    else:
                        await message.answer_document(
                            types.FSInputFile(output_path))
                    sent_files += 1
                except Exception as send_error:
                    logger.error(f"Error sending file {output_path}: {send_error}")
                    await message.answer(f"Не удалось отправить файл {output_filename}")

            else:
                logger.error(f"Watermark failed for {file_path}")
                await message.answer(f"Ошибка при обработке файла {original_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            await message.answer(f"Ошибка при обработке файла {original_path.name}")

    # Final status message
    result_message = (
        f"✅ Готово!\n"
        f"Обработано файлов: {processed_files}/{len(user_data[user_id]['photos'])}\n"
        f"Отправлено файлов: {sent_files}\n\n"
    )

    if processed_files == 0:
        result_message += "Не удалось обработать ни одного файла. Попробуйте снова."
    elif sent_files < processed_files:
        result_message += "Некоторые файлы не были отправлены из-за ошибок."
    else:
        result_message += "Все файлы успешно обработаны и отправлены!"

    await message.answer(
        result_message,
        reply_markup=get_main_keyboard2()
    )

    # Reset state after processing
    user_data[user_id]["state"] = UserState.WAITING_FOR_PHOTOS


@dp.callback_query(lambda c: c.data == "restart")
async def restart_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Delete all files in main user directory
    user_dir = Path(f"files/{user_id}")
    if user_dir.exists():
        for file in user_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
            except Exception as e:
                logger.error(f"Error deleting file {file}: {e}")

    # Delete all files in watermarked subdirectory
    watermarked_dir = Path(f"files/{user_id}/watermarked")
    if watermarked_dir.exists():
        for file in watermarked_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
            except Exception as e:
                logger.error(f"Error deleting watermarked file {file}: {e}")

        # Remove the empty watermarked directory
        try:
            watermarked_dir.rmdir()
        except Exception as e:
            logger.error(f"Error removing watermarked directory: {e}")

    # Reset user data structure
    init_user_data(user_id)

    # Send confirmation message
    await callback.message.answer(
        "Все файлы удалены. Всего файлов: 0\n\n"
        "Пришлите мне одну или несколько фотографий или файлов в формате PNG, JPEG."
    )

@dp.message()
async def text_handler(message: types.Message):
    user_id = message.from_user.id

    # Check subscription for every message
    if not await check_subscription(user_id):
        await message.answer(
            "Для продолжения необходимо подписаться на наш канал.",
            reply_markup=get_subscription_keyboard()
        )
        return

    if user_id not in user_data:
        await message.answer("Пожалуйста, начните с команды /start")
        return

    if user_data[user_id]["state"] == UserState.WAITING_FOR_TEXT:
        # Here you would process the text and photos
        photos_count = len(user_data[user_id]["photos"])
        await message.answer(
            f"Задание создано! Текст: {message.text}\n"
            f"Количество фото: {photos_count}\n\n"
            "Начните заново, если хотите создать новое задание.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="начать заново", callback_data="restart")
            ]])
        )
    else:
        await message.answer("Пожалуйста, пришлите фото или файл")


async def main():
    dp.message.middleware(AlbumMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())