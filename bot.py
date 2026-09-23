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

def crop_image(file_path: str, aspect: str) -> bytes:
    with Image.open(file_path) as img:
        width, height = img.size
        
        if aspect == "1:1":
            new_dim = min(width, height)
            left = (width - new_dim) / 2
            top = (height - new_dim) / 2
            right = (width + new_dim) / 2
            bottom = (height + new_dim) / 2
            img_cropped = img.crop((left, top, right, bottom))
        elif aspect == "16:9":
            target_height = int(width * 9 / 16)
            if target_height > height:
                target_width = int(height * 16 / 9)
                left = (width - target_width) / 2
                img_cropped = img.crop((left, 0, left + target_width, height))
            else:
                top = (height - target_height) / 2
                img_cropped = img.crop((0, top, width, top + target_height))
        elif aspect == "9:16":
            target_width = int(height * 9 / 16)
            if target_width > width:
                target_height = int(width * 16 / 9)
                top = (height - target_height) / 2
                img_cropped = img.crop((0, top, width, top + target_height))
            else:
                left = (width - target_width) / 2
                img_cropped = img.crop((left, 0, left + target_width, height))
        else:
            img_cropped = img

        output = io.BytesIO()
        save_format = img.format if img.format in ["JPEG", "PNG", "WEBP"] else "JPEG"
        if save_format == "JPEG" and img_cropped.mode in ("RGBA", "P"):
            img_cropped = img_cropped.convert("RGB")
        img_cropped.save(output, format=save_format)
        output.seek(0)
        return output.getvalue()

def convert_format(file_path: str, target_format: str) -> bytes:
    with Image.open(file_path) as img:
        output = io.BytesIO()
        fmt = target_format.upper()
        if fmt == "JPG" or fmt == "JPEG":
            fmt = "JPEG"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
        elif fmt == "PNG":
            fmt = "PNG"
        elif fmt == "WEBP":
            fmt = "WEBP"
        else:
            fmt = "JPEG"

        img.save(output, format=fmt)
        output.seek(0)
        return output.getvalue()

def get_main_keyboard(has_exif: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📐 Aspect Ratios (1:1, 16:9, 9:16)", callback_data="menu_aspect")],
        [InlineKeyboardButton(text="🔄 Convert Format (PNG, JPEG, WEBP)", callback_data="menu_format")]
    ]
    if has_exif:
        keyboard.append([InlineKeyboardButton(text="🧹 Strip EXIF", callback_data="strip_exif")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to theexifbot.\n\n"
        "Send me any image to inspect its metadata, crop it into specific dimensions, or convert formats."
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
    keyboard = get_main_keyboard(has_exif)

    await message.answer(metadata_info, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "menu_aspect")
async def cb_menu_aspect(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1:1", callback_data="aspect:1:1"),
            InlineKeyboardButton(text="16:9", callback_data="aspect:16:9"),
            InlineKeyboardButton(text="9:16", callback_data="aspect:9:16")
        ],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_main")]
    ])
    await callback.message.edit_text("Choose aspect ratio for your photo:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "menu_format")
async def cb_menu_format(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="JPEG", callback_data="format:JPEG"),
            InlineKeyboardButton(text="PNG", callback_data="format:PNG"),
            InlineKeyboardButton(text="WEBP", callback_data="format:WEBP")
        ],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_main")]
    ])
    await callback.message.edit_text("Choose target format:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    temp_filename = f"temp_{callback.from_user.id}.jpg"
    if os.path.exists(temp_filename):
        metadata_info, has_exif = get_image_metadata(temp_filename)
        keyboard = get_main_keyboard(has_exif)
        await callback.message.edit_text(metadata_info, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await callback.message.edit_text("⚠️ Session expired. Please send the image again.")
    await callback.answer()

@dp.callback_query(F.data.startswith("aspect:"))
async def cb_apply_aspect(callback: CallbackQuery):
    aspect = callback.data.split(":")[1] + ":" + callback.data.split(":")[2]
    temp_filename = f"temp_{callback.from_user.id}.jpg"
    
    if os.path.exists(temp_filename):
        cropped_bytes = crop_image(temp_filename, aspect)
        photo = BufferedInputFile(cropped_bytes, filename=f"cropped_{aspect.replace(':', '_')}.jpg")
        await callback.message.answer_photo(photo=photo, caption=f"✨ Cropped to {aspect}")
    else:
        await callback.answer("⚠️ Session expired.", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("format:"))
async def cb_apply_format(callback: CallbackQuery):
    fmt = callback.data.split(":")[1]
    temp_filename = f"temp_{callback.from_user.id}.jpg"
    
    if os.path.exists(temp_filename):
        converted_bytes = convert_format(temp_filename, fmt)
        ext = fmt.lower()
        photo = BufferedInputFile(converted_bytes, filename=f"converted_image.{ext}")
        await callback.message.answer_document(document=photo, caption=f"✨ Converted to {fmt}")
    else:
        await callback.answer("⚠️ Session expired.", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "strip_exif")
async def callback_strip_exif(callback: CallbackQuery):
    temp_filename = f"temp_{callback.from_user.id}.jpg"
    if os.path.exists(temp_filename):
        with Image.open(temp_filename) as img:
            data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)
            output = io.BytesIO()
            save_format = img.format if img.format in ["JPEG", "PNG", "WEBP"] else "JPEG"
            clean_img.save(output, format=save_format)
            output.seek(0)
            clean_bytes = output.getvalue()

        clean_photo = BufferedInputFile(clean_bytes, filename="clean_image.jpg")
        await callback.message.answer_photo(photo=clean_photo, caption="✨ EXIF metadata removed.")
    else:
        await callback.answer("⚠️ Session expired.", show_alert=True)
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("theexifbot is running with extended tools!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

