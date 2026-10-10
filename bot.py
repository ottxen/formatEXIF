import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Отримуємо токен з змінних середовища Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у змінних середовища!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Зберігання обраної мови користувачів (у пам'яті)
user_languages = {}

TEXTS = {
    "en": {
        "welcome": "Welcome to Sports Pulse Bot! 🏆\nSelect a sport category below:",
        "motorsport_menu": "🏎 Choose a motorsport discipline:",
        "football_menu": "⚽ **Latest Football News:**\n\n1. Champions League group stage highlights\n2. Transfer window updates and rumors\n3. Weekend derby preview",
        "basketball_menu": "🏀 **Latest Basketball News:**\n\n1. NBA playoffs race heats up\n2. Stunning buzzer-beater ends last night's game\n3. Injury reports and team updates",
        "f1_news": "🏁 **Latest Formula 1 News:**\n\n1. Leclerc sets the pace in practice\n2. McLaren announces a major upgrade package\n3. Antonelli prepares for the upcoming Grand Prix",
        "motogp_news": "🏍 **Latest MotoGP News:**\n\n1. Márquez claims thrilling pole position\n2. Championship battle tightens after wet race\n3. Factory teams test new aerodynamics",
        "btn_football": "⚽ Football",
        "btn_basketball": "🏀 Basketball",
        "btn_motorsport": "🏍 Motorsport",
        "btn_lang": "🌐 Мова: Українська 🇺🇦",
        "btn_back": "⬅️ Back",
    },
    "ua": {
        "welcome": "Ласкаво просимо до Sports Pulse Bot! 🏆\nОберіть категорію спорту нижче:",
        "motorsport_menu": "🏎 Оберіть дисципліну мотоспорту:",
        "football_menu": "⚽ **Останні новини футболу:**\n\n1. Найяскравіші моменти Ліги Чемпіонів\n2. Новини трансферного вікна та чутки\n3. Прев'ю центрального матчу туру",
        "basketball_menu": "🏀 **Останні новини баскетболу:**\n\n1. Боротьба за плей-оф в НБА загострюється\n2. Неймовірний кидок на останній секунді\n3. Оновлення щодо травм та складу команд",
        "f1_news": "🏁 **Останні новини Формули-1:**\n\n1. Леклер показує найкращий час у вільних заїздах\n2. McLaren анонсує великий пакет оновлень\n3. Антонеллі готується до майбутнього Гран-прі",
        "motogp_news": "🏍 **Останні новини MotoGP:**\n\n1. Маркес виборює захопливу поул-позицію\n2. Боротьба за чемпіонство загострюється після дощової гонки\n3. Заводські команди тестують нову аеродинаміку",
        "btn_football": "⚽ Футбол",
        "btn_basketball": "🏀 Баскетбол",
        "btn_motorsport": "🏍 Мотоспорт",
        "btn_lang": "🌐 Language: English 🇬🇧",
        "btn_back": "⬅️ Назад",
    }
}

def get_main_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS[lang]["btn_football"], callback_data="news_football")
    builder.button(text=TEXTS[lang]["btn_basketball"], callback_data="news_basketball")
    builder.button(text=TEXTS[lang]["btn_motorsport"], callback_data="menu_motorsport")
    builder.button(text=TEXTS[lang]["btn_lang"], callback_data="toggle_language")
    builder.adjust(2, 1, 1)
    return builder.as_markup()

def get_motorsport_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🏎 Formula 1", callback_data="news_f1")
    builder.button(text="🏍 MotoGP", callback_data="news_motogp")
    builder.button(text=TEXTS[lang]["btn_back"], callback_data="menu_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_back_keyboard(lang: str, back_callback: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS[lang]["btn_back"], callback_data=back_callback)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = "en"  # За замовчуванням англійська
    
    lang = user_languages[user_id]
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data == "toggle_language")
async def toggle_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_lang = user_languages.get(user_id, "en")
    new_lang = "ua" if current_lang == "en" else "en"
    user_languages[user_id] = new_lang
    
    await callback.message.edit_text(
        TEXTS[new_lang]["welcome"], 
        reply_markup=get_main_keyboard(new_lang)
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_main")
async def menu_main(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data == "menu_motorsport")
async def menu_motorsport(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(TEXTS[lang]["motorsport_menu"], reply_markup=get_motorsport_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data == "news_football")
async def news_football(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(
        TEXTS[lang]["football_menu"],
        reply_markup=get_back_keyboard(lang, "menu_main"),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "news_basketball")
async def news_basketball(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(
        TEXTS[lang]["basketball_menu"],
        reply_markup=get_back_keyboard(lang, "menu_main"),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "news_f1")
async def news_f1(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(
        TEXTS[lang]["f1_news"], 
        reply_markup=get_back_keyboard(lang, "menu_motorsport"),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "news_motogp")
async def news_motogp(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(
        TEXTS[lang]["motogp_news"], 
        reply_markup=get_back_keyboard(lang, "menu_motorsport"),
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
