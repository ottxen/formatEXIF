import asyncio
import io
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from PIL import Image
from PIL.ExifTags import TAGS

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_image_metadata(file_path: str) -> tuple[str, bool]:
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

            info_text = (
                f"📷 **Image Technical Info:**\n\n"
                f"• **Format:** {format_name}\n"
                f"• **Resolution:** {width}x{height} px\n"
                f"• **Color Mode:** {mode}\n"
                f"• **File Size:** {file_size_kb} KB\n"
            )

            exif_data = img.getexif()
            has_exif = bool(exif_data)
            
            if has_exif:
                info_text += "\n📍 **EXIF Data:**\n"
                exif_found = False
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ["Make", "Model", "DateTime", "ExposureTime", "FNumber", "ISOSpeedRatings"]:
                        info_text += f"• **{tag}:** {value}\n"
                        exif_found = True
                
                if not exif_found:
                    info_text += "_No standard EXIF tags found._"
            else:
                info_text += "\n_No EXIF data available._"

            return info_text, has_exif
    except Exception as e:
        return f"❌ Error reading image metadata: {e}", False

def remove_exif_bytes(file_path: str) -> bytes:
    """Видаляє метадані та повертає байти чистого зображення."""
    with Image.open(file_path) as img:
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        
        output = io.BytesIO()
        # Зберігаємо у початковому форматі або за замовчуванням у JPEG
        save_format = img.format if img.format in ["JPEG", "PNG"] else "JPEG"
        clean_img.save(output, format=save_format)
        output.seek(0)
        return output.getvalue()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to theexifbot.\n\n"
        "Send me any image, and I will instantly show its technical properties, EXIF data, and let you strip metadata if needed."
    )

@dp.message(F.photo)
async def handle_photo(message: Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path

    downloaded_file = await bot.download_file(file_path)
    
    temp_filename = f"temp_{message.from_user.id}.jpg"
    with open(temp_filename, "wb") as f:
        f.write(downloaded_file.read())

    metadata_info, has_exif = get_image_metadata(temp_filename)

    keyboard = None
    if has_exif:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Strip EXIF (Send Clean Photo)", callback_data="strip_exif")]
        ])

    # Зберігаємо шлях до файлу у стейт або просто передаємо черездію (для простоти поки збережемо у тимчасовому файлі, але краще обробити шлях). 
    # Щоб кнопка спрацювала, запишемо шлях у словник за ID користувача або передамо в cache.
    # Для базової реалізації зробимо простіше:
    await message.answer(metadata_info, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "strip_exif")
async def callback_strip_exif(callback: CallbackQuery):
    temp_filename = f"temp_{callback.from_user.id}.jpg"
    if os.path.exists(temp_filename):
        clean_bytes = remove_exif_bytes(temp_filename)
        clean_photo = BufferedInputFile(clean_bytes, filename="clean_image.jpg")
        
        await callback.message.answer_photo(
            photo=clean_photo,
            caption="✨ Here is your clean image with all EXIF metadata removed."
        )
        os.remove(temp_filename)
    else:
        await callback.answer("⚠️ Session expired. Please send the image again.", show_alert=True)
    
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("theexifbot is running with EXIF stripping!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
