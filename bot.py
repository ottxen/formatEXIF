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

def get_image_analysis(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    format_name = img.format or "UNKNOWN"
    color_mode = img.mode
    file_size_kb = len(image_bytes) / 1024
    
    # Розрахунок мегапікселів та орієнтації
    megapixels = round((width * height) / 1_000_000, 2)
    orientation = "Portrait" if height > width else ("Landscape" if width > height else "Square")
    aspect_gcd = f"{width}:{height}" # спрощено для мінімалізму
    
    # Збір EXIF даних
    exif_data = {}
    camera_model = "Unknown"
    iso = "Unknown"
    shutter = "Unknown"
    aperture = "Unknown"
    focal = "Unknown"
    taken_date = "Unknown"
    
    try:
        raw_exif = img.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "Model":
                    camera_model = str(value).strip()
                elif tag == "ISOSpeedRatings":
                    iso = str(value)
                elif tag == "ExposureTime":
                    shutter = f"1/{round(1/float(value))}" if float(value) < 1 else str(value)
                elif tag == "FNumber":
                    aperture = f"f/{float(value)}"
                elif tag == "FocalLength":
                    focal = f"{int(value)}mm"
                elif tag == "DateTimeOriginal":
                    taken_date = str(value)
    except Exception:
        pass

    has_exif = camera_model != "Unknown" or taken_date != "Unknown"

    # Формування красивого виводу у твоєму стилі
    output = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▪ THEEXIFBOT ‖ INSPECTOR\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **Image Health & Tech**\n"
        f"│ ▪ Format: `{format_name}`\n"
        f"│ ▪ Resolution: `{width}x{height} px` (`{megapixels} MP`)\n"
        f"│ ▪ Size: `{file_size_kb:.2f} KB`\n"
        f"│ ▪ Color Mode: `{color_mode}`\n"
        f"│ ▪ Orientation: `{orientation}`\n\n"
    )

    if has_exif:
        output += (
            "📷 **Camera Info (EXIF)**\n"
            f"│ ▪ Camera: `{camera_model}`\n"
            f"│ ▪ ISO: `{iso}` ‖ Shutter: `{shutter}`\n"
            f"│ ▪ Aperture: `{aperture}` ‖ Focal: `{focal}`\n"
            f"│ ▪ Taken: `{taken_date}`\n\n"
        )
    else:
        output += "📷 **Camera Info:** `No EXIF data available.`\n\n"

    output += "▫ Status: Ready for utility actions."
    return output

def get_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✂️ Crop (1:1, 16:9)", callback_data="action:crop"),
         InlineKeyboardButton(text="🔄 Convert Format", callback_data="action:convert")],
        [InlineKeyboardButton(text="🛡️ Strip EXIF", callback_data="action:strip"),
         InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▪ THEEXIFBOT ‖ UTILITY\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send me any image to inspect its technical info, EXIF data, or process it."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.photo)
async def handle_photo(message: Message):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    image_bytes = downloaded_file.read()
    
    analysis_report = get_image_analysis(image_bytes)
    
    await message.answer(
        analysis_report,
        reply_markup=get_action_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("action:"))
async def cb_action(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    await callback.answer(f"Action '{action}' selected. (Feature in progress)")

@dp.callback_query(F.data == "back_main")
async def cb_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "▪ THEEXIFBOT ‖ Send me any image to inspect.",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("theexifbot is running with enhanced metrics!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
