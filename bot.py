import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from PIL import Image
from PIL.ExifTags import TAGS

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def get_image_metadata(file_path: str) -> str:
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
            if exif_data:
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

            return info_text
    except Exception as e:
        return f"❌ Error reading image metadata: {e}"


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to theexifbot.\n\n"
        "Send me any image, and I will instantly show its technical properties and EXIF data."
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path

    downloaded_file = await bot.download_file(file_path)
    
    temp_filename = "temp_image.jpg"
    with open(temp_filename, "wb") as f:
        f.write(downloaded_file.read())

    metadata_info = get_image_metadata(temp_filename)

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    await message.answer(metadata_info, parse_mode="Markdown")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("theexifbot is running!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
      
