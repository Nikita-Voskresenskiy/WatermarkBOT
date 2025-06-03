import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import logging
import os
from pathlib import Path
from watermark_algorithm import apply_watermark

import json

with open('settings.json', 'r', encoding='utf-8') as file:
    settings = json.load(file)


# Bot setup
TOKEN = settings["token"]
CHANNEL_ID = settings["channel_id"]  # Private channel ID (negative for channels)
ADMIN_ID = settings["admin_id"]  # Your admin ID for logs
CHANNEL_USERNAME = settings["channel_username"]

bot = Bot(token=TOKEN)
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
        "photos": [],
        "watermarked_photos": [],
        "watermark_text": None,
        # Add any other fields you might need in the future
    }

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription for {user_id}: {e}")
        return False


def get_subscription_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Подписаться на канал",
        url=f"https://t.me/{CHANNEL_USERNAME}")  # Replace with your channel username
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
        text="задать текст",
        callback_data="to_text")
    )
    builder.add(InlineKeyboardButton(
        text="начать заново",
        callback_data="restart")
    )
    return builder.as_markup()


@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.answer("Вы подписаны на канал! Спасибо!", show_alert=True)
        await start_handler(callback.message)
    else:
        await callback.answer("Вы еще не подписаны на канал!", show_alert=True)


@dp.message(F.photo | F.document)
async def handle_files(message: types.Message):
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

    # Create user directory if it doesn't exist
    user_dir = Path(f"files/{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Handle photo
        if message.photo:
            file_id = message.photo[-1].file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path
            ext = os.path.splitext(file_path)[1] or ".jpg"  # Default to .jpg for photos
            dest = user_dir / f"photo_{len(user_data[user_id]['photos'])}{ext}"
            await bot.download_file(file_path, destination=dest)
            user_data[user_id]["photos"].append(str(dest))

        # Handle document
        elif message.document:
            mime_type = message.document.mime_type
            if mime_type in ['image/jpeg', 'application/prg']:
                file_id = message.document.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path
                filename = message.document.file_name or os.path.basename(file_path)
                dest = user_dir / filename
                await bot.download_file(file_path, destination=dest)
                user_data[user_id]["photos"].append(str(dest))
            else:
                await message.answer("Неподдерживаемый формат файла. Пришлите JPEG или PRG.")
                return

        await message.answer(
            f"Файл сохранен. Всего файлов: {len(user_data[user_id]['photos'])}\n\n"
            "Вы можете прислать еще фото или перейти к заданию текста или начать заново.",
            reply_markup=get_main_keyboard()
        )

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
    await callback.message.answer("Теперь введите текст для watermark:")


@dp.message(F.text)
async def handle_watermark_text(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id]["state"] != UserState.WAITING_FOR_TEXT:
        await message.answer("Пожалуйста, сначала отправьте фото и нажмите 'перейти к заданию текста'")
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
                            types.FSInputFile(output_path),
                            caption=f"Файл с водяным знаком: {watermark_text}"
                        )
                    else:
                        await message.answer_document(
                            types.FSInputFile(output_path),
                            caption=f"Файл с водяным знаком: {watermark_text}"
                        )
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
        reply_markup=get_main_keyboard()
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
        "Пришлите мне одну или несколько фотографий или файлов в формате PNG, JPEG.",
        reply_markup=get_main_keyboard()
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())