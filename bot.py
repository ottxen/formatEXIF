import asyncio
import os
import feedparser
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у змінних середовища Railway!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Пам'ять для обраної мови
user_languages = {}

# Перевірені та стабільні RSS-джерела
RSS_FEEDS = {
    "en": {
        "football": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "basketball": "https://www.espn.com/espn/rss/nba/news",
        "motorsport": "https://www.motorsport.com/rss/f1/news/",
        "ufc": "https://www.espn.com/espn/rss/mma/news",
        "tennis": "https://feeds.bbci.co.uk/sport/tennis/rss.xml",
        "esports": "https://www.hltv.org/rss/news"
    },
    "ua": {
        "football": "https://footboom1.com/uk/rss/news.xml",
        "basketball": "https://fbu.ua/rss/news",
        "motorsport": "https://ua.motorsport.com/rss/f1/news/",
        "ufc": "https://sport.ua/rss/allnews",
        "tennis": "https://btf.ua/feed/",
        "esports": "https://gameinside.ua/feed/"
    }
}

UI_TEXTS = {
    "en": {
        "welcome": "🏆 **Sports Pulse Bot**\nSelect a category to fetch the latest real-time news:",
        "btn_football": "⚽ Football",
        "btn_basketball": "🏀 Basketball",
        "btn_motorsport": "🏎 Motorsport (F1)",
        "btn_ufc": "🥊 UFC / MMA",
        "btn_tennis": "🎾 Tennis",
        "btn_esports": "🎮 Esports",
        "btn_lang": "🌐 Мова: Українська 🇺🇦",
        "btn_back": "⬅️ Back",
        "fetching": "⏳ Fetching latest news...",
        "no_news": "❌ Could not load news at the moment. Try again later."
    },
    "ua": {
        "welcome": "🏆 **Sports Pulse Bot**\nОберіть категорію, щоб отримати найновіші реальні новини:",
        "btn_football": "⚽ Футбол",
        "btn_basketball": "🏀 Баскетбол",
        "btn_motorsport": "🏎 Мотоспорт (F1)",
        "btn_ufc": "🥊 UFC / MMA",
        "btn_tennis": "🎾 Теніс",
        "btn_esports": "🎮 Кіберспорт",
        "btn_lang": "🌐 Language: English 🇬🇧",
        "btn_back": "⬅️ Назад",
        "fetching": "⏳ Завантажую найновіші новини...",
        "no_news": "❌ Не вдалося завантажити новини. Спробуйте пізніше."
    }
}

# Функція завантаження новин з імітацією браузера
def fetch_latest_news(sport: str, lang: str, count: int = 5):
    feed_url = RSS_FEEDS.get(lang, {}).get(sport)
    if not feed_url:
        return []

    try:
        # Заголовки, щоб сайти сприймали бота як звичайний браузер Chrome
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Отримуємо контент через requests
        response = requests.get(feed_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Помилка HTTP {response.status_code} для {feed_url}")
            return []

        # Парсимо отриманий XML
        feed = feedparser.parse(response.content)
        articles = []
        
        for entry in feed.entries[:count]:
            title = entry.title
            
            # Очищення та обрізання опису
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            # Видаляємо HTML теги якщо вони є
            if "<" in summary and ">" in summary:
                import re
                summary = re.sub('<[^<]+?>', '', summary)
                
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            link = entry.link
            articles.append((title, summary, link))
            
        return articles
    except Exception as e:
        print(f"Помилка парсингу RSS ({sport}/{lang}): {e}")
        return []

# Клавіатури
def get_main_keyboard(lang: str):
    b = InlineKeyboardBuilder()
    b.button(text=UI_TEXTS[lang]["btn_football"], callback_data="sport_football")
    b.button(text=UI_TEXTS[lang]["btn_basketball"], callback_data="sport_basketball")
    b.button(text=UI_TEXTS[lang]["btn_motorsport"], callback_data="sport_motorsport")
    b.button(text=UI_TEXTS[lang]["btn_ufc"], callback_data="sport_ufc")
    b.button(text=UI_TEXTS[lang]["btn_tennis"], callback_data="sport_tennis")
    b.button(text=UI_TEXTS[lang]["btn_esports"], callback_data="sport_esports")
    b.button(text=UI_TEXTS[lang]["btn_lang"], callback_data="toggle_language")
    b.adjust(2, 2, 2, 1)
    return b.as_markup()

def get_back_keyboard(lang: str):
    b = InlineKeyboardBuilder()
    b.button(text=UI_TEXTS[lang]["btn_back"], callback_data="menu_main")
    return b.as_markup()

# Обробники команд
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = "en"
    lang = user_languages[user_id]
    await message.answer(UI_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data == "toggle_language")
async def toggle_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_lang = user_languages.get(user_id, "en")
    new_lang = "ua" if current_lang == "en" else "en"
    user_languages[user_id] = new_lang
    
    await callback.message.edit_text(UI_TEXTS[new_lang]["welcome"], reply_markup=get_main_keyboard(new_lang))
    await callback.answer()

@dp.callback_query(F.data == "menu_main")
async def menu_main(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "en")
    await callback.message.edit_text(UI_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))
    await callback.answer()

@dp.callback_query(F.data.startswith("sport_"))
async def show_real_news(callback: types.CallbackQuery):
    sport = callback.data.split("_")[1]
    lang = user_languages.get(callback.from_user.id, "en")

    await callback.answer(UI_TEXTS[lang]["fetching"])

    # Отримуємо новини у фоновому потоці
    loop = asyncio.get_event_loop()
    articles = await loop.run_in_executor(None, fetch_latest_news, sport, lang, 5)

    if not articles:
        await callback.message.edit_text(
            UI_TEXTS[lang]["no_news"],
            reply_markup=get_back_keyboard(lang)
        )
        return

    header = "🔥 **Latest News:**\n\n" if lang == "en" else "🔥 **Останні свіжі новини:**\n\n"
    text = header
    
    for i, (title, summary, link) in enumerate(articles, 1):
        text += f"**{i}. [{title}]({link})**\n"
        if summary:
            text += f"_{summary}_\n"
        text += "\n───────────────────\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(lang),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def main():
    print("Бот зі стабільним RSS завантаженням запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
