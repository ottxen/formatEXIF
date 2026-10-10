import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у змінних середовища!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Зберігання обраної мови користувачів
user_languages = {}

# Тексти інтерфейсу (UA та EN)
UI_TEXTS = {
    "en": {
        "welcome": "🏆 **Sports Pulse Bot**\nSelect a sport category to read detailed news and archives:",
        "date_prompt": "📅 Choose the timeframe or date for news:",
        "btn_football": "⚽ Football",
        "btn_basketball": "🏀 Basketball",
        "btn_motorsport": "🏍 Motorsport (F1 / MotoGP)",
        "btn_ufc": "🥊 UFC & MMA",
        "btn_tennis": "🎾 Tennis",
        "btn_esports": "🎮 Esports (CS2/Dota)",
        "btn_lang": "🌐 Мова: Українська 🇺🇦",
        "btn_today": "🔥 Today's Highlights",
        "btn_yesterday": "⏮ Yesterday",
        "btn_two_days": "📜 2 Days Ago",
        "btn_archive": "🗓 Month Archive",
        "btn_back": "⬅️ Back",
    },
    "ua": {
        "welcome": "🏆 **Sports Pulse Bot**\nОберіть категорію спорту, щоб читати детальні новини та архіви:",
        "date_prompt": "📅 Оберіть період або день для перегляду новин:",
        "btn_football": "⚽ Футбол",
        "btn_basketball": "🏀 Баскетбол",
        "btn_motorsport": "🏍 Мотоспорт (F1 / MotoGP)",
        "btn_ufc": "🥊 UFC та MMA",
        "btn_tennis": "🎾 Теніс",
        "btn_esports": "🎮 Кіберспорт (CS2/Dota)",
        "btn_lang": "🌐 Language: English 🇬🇧",
        "btn_today": "🔥 Головне сьогодні",
        "btn_yesterday": "⏮ Вчора",
        "btn_two_days": "📜 2 дні тому",
        "btn_archive": "🗓 Архів за місяць",
        "btn_back": "⬅️ Назад",
    }
}

# Детальна база новин за спортом та датами (симуляція великого архіву)
NEWS_DATABASE = {
    "football": {
        "today": [
            ("⚽ Ексклюзив: Поворотний момент у Лізі Чемпіонів", "Аналітики обговорюють сенсаційну тактику аутсайдера, яка шокувала чинного чемпіона. Тренер зробив ризиковану заміну на 70-й хвилині, що повністю перевернула хід гри на користь команди."),
            ("⚽ Трансферні новини: Зірковий форвард готується до переходу", "За інсайдерськими даними, переговори між клубами вийшли на фінальну пряму. Сума трансферу може скласти рекордні 120 мільйонів євро, а контракт підпишуть до кінця тижня.")
        ],
        "yesterday": [
            ("⚽ Підсумки центрального матчу туру", "Напружене дербі завершилося з рахунком 2:2. Суддівський комітет вже прокоментував спірний епізод із пенальті на останніх хвилинах матчу, визнавши рішення арбітра правильним."),
            ("⚽ Травма ключового півзахисника", "Медичний штаб збірної підтвердив пошкодження гравця. Відновлення займе близько трьох тижнів, через що він пропустить найближчі матчі єврокубків.")
        ]
    },
    "motorsport": {
        "today": [
            ("🏁 F1: Велике оновлення боліда перед Гран-прі", "Команда привезла на трек абсолютно новий пакет аеродинаміки: змінено форму понтонів та днища. Пілоти відзначають покращення стабільності в повільних поворотах під час перших вільних заїздів."),
            ("🏍 MotoGP: Неймовірна боротьба за поул", "Кваліфікація подарувала фанатам справжнє шоу: доля першого місця вирішилася на останніх мікросекундах завдяки блискучому проходженню фінального сектору.")
        ],
        "yesterday": [
            ("🏁 Засідання комісії FIA: нові правила на наступний сезон", "Сьогодні обговорювалися зміни до технічного регламенту силових установок. Команди досягли компромісу щодо обмеження бюджетів та екологічних стандартів палива."),
            ("🏁 Інтерв'ю молодих пілотів академії", "Перспективні гонщики поділилися думками про свій шлях у картині молодших серій та підготовку до переходу у вищий дивізіон.")
        ]
    },
    "esports": {
        "today": [
            ("🎮 CS2 Major: Сенсаційний виліт фаворитів", "Турнір приносить шокуючі результати: одна з найстабільніших команд світу поступилася у нижній сітці після трьох напружених мап на Overpass та Mirage."),
            ("🎮 Dota 2 патч: оновлення балансу героїв", "Розробники випустили виправлення помилок та підкоригували характеристики ключових персонажів меті перед стартом міжнародних кваліфікацій.")
        ],
        "yesterday": [
            ("🎮 Гранд-фінал турніру: рекордні цифри глядачів", "Піковий онлайн трансляції перевищив 1.2 мільйона глядачів. Серія тривала понад 4 години і завершилася драматичним камбеком на п'ятій мапі.")
        ]
    },
    "basketball": {
        "today": [
            ("🏀 НБА: Рекорд результативності нічного матчу", "Зірковий розігруючий оформив трипл-дабл з показником у 45 очок, 12 підборів та 14 асистів, встановивши особистий рекорд сезону.")
        ],
        "yesterday": [
            ("🏀 Тактичний розбір гри лідерів чемпіонату", "Як змінилася захисна схема команди після зміни головного тренера та чому статистика підбирань стала ключем до перемоги.")
        ]
    },
    "ufc": {
        "today": [
            ("🥊 Офіційно анонсовано бій за чемпіонський пояс", "Президент промоушну підтвердив головну подію вечора на наступний місяць. Претендент вже розпочав підготовку у тренувальному таборі.")
        ],
        "yesterday": [
            ("🥊 Післяматчеві скандали та слова бійців", "Що сказали спортсмени одне одному одразу після завершення кривавого п'ятираундового поєдинку в октагоні.")
        ]
    },
    "tennis": {
        "today": [
            ("🎾 Шоломи: Сенсація на корщені престижного турніру", "Чинний чемпіон вибув у другому раунді від маловідомого тенісиста з другої сотні світового рейтингу.")
        ],
        "yesterday": [
            ("🎾 Оновлення світового рейтингу ATP та WTA", "Хто з українських тенісистів піднявся у списку найкращих гравців світу за підсумками минулого тижня.")
        ]
    }
}

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

def get_date_keyboard(lang: str, sport: str):
    b = InlineKeyboardBuilder()
    b.button(text=UI_TEXTS[lang]["btn_today"], callback_data=f"news_{sport}_today")
    b.button(text=UI_TEXTS[lang]["btn_yesterday"], callback_data=f"news_{sport}_yesterday")
    b.button(text=UI_TEXTS[lang]["btn_two_days"], callback_data=f"news_{sport}_twodays")
    b.button(text=UI_TEXTS[lang]["btn_archive"], callback_data=f"news_{sport}_archive")
    b.button(text=UI_TEXTS[lang]["btn_back"], callback_data="menu_main")
    b.adjust(1, 2, 1, 1)
    return b.as_markup()

def get_back_keyboard(lang: str, sport: str):
    b = InlineKeyboardBuilder()
    b.button(text=UI_TEXTS[lang]["btn_back"], callback_data=f"sport_{sport}")
    return b.as_markup()

# Обробники
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = "ua" # За замовчуванням українська для зручності
    lang = user_languages[user_id]
    await message.answer(UI_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data == "toggle_language")
async def toggle_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_lang = user_languages.get(user_id, "ua")
    new_lang = "en" if current_lang == "ua" else "ua"
    user_languages[user_id] = new_lang
    await callback.message.edit_text(UI_TEXTS[new_lang]["welcome"], reply_markup=get_main_keyboard(new_lang))
    await callback.answer()

@dp.callback_query(F.data == "menu_main")
async def menu_main(callback: types.CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "ua")
    await callback.message.edit_text(UI_TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))
    await callback.answer()

# Вибір спорту -> вибір дати
@dp.callback_query(F.data.startswith("sport_"))
async def select_sport(callback: types.CallbackQuery):
    sport = callback.data.split("_")[1]
    lang = user_languages.get(callback.from_user.id, "ua")
    await callback.message.edit_text(
        f"📌 Ви обрали категорію. {UI_TEXTS[lang]['date_prompt']}",
        reply_markup=get_date_keyboard(lang, sport)
    )
    await callback.answer()

# Перегляд новин за конкретною датою
@dp.callback_query(F.data.startswith("news_"))
async def show_news(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    sport = parts[1]
    date_key = parts[2]
    lang = user_languages.get(callback.from_user.id, "ua")

    # Отримуємо новини або дефолтний текст якщо архів пустий
    sport_data = NEWS_DATABASE.get(sport, {})
    articles = sport_data.get(date_key, [
        ("📁 Інформація оновлюється", "За цей період поки немає детальних публікацій у базі. Спробуйте обрати «Сьогодні» або «Вчора».")
    ])

    # Формуємо красивий текст новин
    date_titles = {
        "today": "🔥 Головні події за сьогодні:",
        "yesterday": "⏮ Новини за вчора:",
        "twodays": "📜 Архів за 2 дні тому:",
        "archive": "🗓 Розширений місячний архів:"
    }

    text = f"**{date_titles.get(date_key, 'Архів новин')}**\n\n"
    for i, (title, desc) in enumerate(articles, 1):
        text += f"**{i}. {title}**\n{desc}\n\n───────────────────\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(lang, sport),
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    print("Бот зі спортивним архівом запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
