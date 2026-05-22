import telebot
from telebot import types
import json
import os
import threading
import requests
import time
import random

TOKEN = '8736300910:AAEeVFzPEUlwuvY67irIGZUCy96pT94QVa4'
MANAGER_IDS = [545304840]  # Список ID менеджеров (можно добавить нескольких)

bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
ACTIVE_FILE = 'active_conversations.json'
USERS_FILE = 'users.json'

# Время работы поддержки (по Москве)
SUPPORT_START_HOUR = 10  # 10:00
SUPPORT_END_HOUR = 22    # 22:00

# -------------------------------------------------------------------
# Функция для пинга (держит бота активным на Render)
# -------------------------------------------------------------------
def keep_alive():
    url = "https://street-beat-bot.onrender.com"  # ЗАМЕНИТЕ НА ВАШ URL после деплоя
    while True:
        try:
            requests.get(url, timeout=10)
            print("✅ Пинг отправлен")
        except Exception as e:
            print(f"❌ Ошибка пинга: {e}")
        time.sleep(600)  # Каждые 10 минут


def is_support_working():
    """Проверяет, работает ли поддержка сейчас"""
    now = dadetime.datetime.now()
    current_hour = now.hour
    return SUPPORT_START_HOUR <= current_hour < SUPPORT_END_HOUR


def get_support_status_message():
    """Возвращает сообщение о статусе работы поддержки"""
    if is_support_working():
        return None
    else:
        return (
            "😔 *Поддержка сейчас не работает*\n\n"
            f"🕐 Время работы: {SUPPORT_START_HOUR}:00 - {SUPPORT_END_HOUR}:00 (МСК)\n\n"
            "Вы можете:\n"
            "• Написать нам — ответим утром\n"
            "• Посмотреть информацию в кнопках «Доставка», «Оплата и возврат»\n"
            "• Посетить наш магазин через кнопку «Магазин»\n\n"
            "❓ Если вопрос срочный, оставьте сообщение — мы ответим в рабочее время!"
        )

# -------------------------------------------------------------------
# Работа с файлами
# -------------------------------------------------------------------
def load_active():
    if os.path.exists(ACTIVE_FILE):
        with open(ACTIVE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_active(active):
    with open(ACTIVE_FILE, 'w') as f:
        json.dump(active, f)


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


# -------------------------------------------------------------------
# Клавиатуры
# -------------------------------------------------------------------
def user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛍️ Магазин", "❓ Помощь")
    markup.row("🚚 Доставка", "💳 Оплата и возврат")
    markup.row("📏 Таблица размеров", "📞 Контакты")
    markup.row("👤 Связаться с поддержкой")
    return markup


def support_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("❌ Завершить диалог")
    return markup


def manager_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Активные чаты", "📊 Статистика")
    markup.row("⚙️ Помощь")
    return markup


# -------------------------------------------------------------------
# ТИПЫ ВОПРОСОВ ДЛЯ ПОДДЕРЖКИ
# -------------------------------------------------------------------
QUESTION_TYPES = {
    "🔄 По возврату": "Вопрос по возврату или обмену",
    "⭐ Качество обслуживания": "Отзыв о качестве обслуживания",
    "🚚 По доставке": "Вопрос по доставке",
    "💳 По оплате": "Вопрос по оплате",
    "📏 По размерам": "Помощь с выбором размера",
    "🎁 По подарочным картам": "Вопрос по подарочным картам",
    "🔧 По гарантии": "Вопрос по гарантийному обслуживанию",
    "💰 По цене": "Вопрос по цене и скидкам",
    "🏷️ По текущим акциям": "Вопрос по текущим акциям и скидкам",
    "📝 Другое": "Другой вопрос"
}

# Временное хранилище выбранного типа вопроса для каждого пользователя
user_question_type = {}


def question_type_keyboard():
    """Клавиатура с типами вопросов"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = []
    for q_type in QUESTION_TYPES.keys():
        buttons.append(types.KeyboardButton(q_type))
    markup.add(*buttons)
    markup.add(types.KeyboardButton("◀️ Отмена"))
    return markup


# -------------------------------------------------------------------
# Таблица размеров (бренды и file_id)
# -------------------------------------------------------------------
BRANDS = [
    "Adidas", "Birkenstock", "Converse", "Dr. Martens", "Hikes",
    "Jordan", "Napapijri", "New Balance", "Nike", "Palladium",
    "Puma", "Reebok", "Salomon", "STREETBEAT", "Timberland", "Vans"
]

# Словарь с file_id таблиц размеров
SIZE_TABLES = {
    "Adidas": {
        "male": "AgACAgIAAxkBAAICP2oPERSU1iOXwV5d_mt2OzDFrNQiAAKbHWsbrOZ4SMWUgqVf8tH-AQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICXWoPFRlfjeF4t9HMfe5kyxbtiOEmAALCHWsbrOZ4SBS5Ezqdrz64AQADAgADeQADOwQ"
    },
    "Birkenstock": {
        "male": "AgACAgIAAxkBAAICUWoPE2-49JLaIBS0IIhzgn8CE8eHAAKuHWsbrOZ4SIX0vunRZ00BAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICUWoPE2-49JLaIBS0IIhzgn8CE8eHAAKuHWsbrOZ4SIX0vunRZ00BAQADAgADeQADOwQ"
    },
    "Converse": {
        "male": "AgACAgIAAxkBAAICSWoPEmbkoyd9XUvlS0xvxyU-mvn0AAKnHWsbrOZ4SPb9fMjulX8WAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICZ2oPFknrI6ccNF6BBAG41OlTVwTEAALSHWsbrOZ4SBvd1DkqxJGUAQADAgADeQADOwQ"
    },
    "Dr. Martens": {
        "male": "AgACAgIAAxkBAAICTWoPEveSKYQN6NZqyg-YCNLKVcsbAAKrHWsbrOZ4SOVYJQHhRukeAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICa2oPFtSXJVxe59WOSwSJ1PKdQSVrAALYHWsbrOZ4SPsQRYhNXA69AQADAgADeQADOwQ"
    },
    "Hikes": {
        "male": "AgACAgIAAxkBAAICU2oPE6nXsazZq25H5kLyeZLGctN-AAKvHWsbrOZ4SNzm7m2L-3ibAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICU2oPE6nXsazZq25H5kLyeZLGctN-AAKvHWsbrOZ4SNzm7m2L-3ibAQADAgADeQADOwQ"
    },
    "Jordan": {
        "male": "AgACAgIAAxkBAAICPWoPENhS_TOAenopOUrRtX2mfINcAAKZHWsbrOZ4SAewJBIqocpZAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICPWoPENhS_TOAenopOUrRtX2mfINcAAKZHWsbrOZ4SAewJBIqocpZAQADAgADeQADOwQ"
    },
    "Napapijri": {
        "male": "AgACAgIAAxkBAAICT2oPEynuFRfJto4Qt6_Kl3t_UpPrAAKtHWsbrOZ4SEpaaWbRLzC4AQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICbWoPFxg9EChD9RV6oD2MHReyoOY7AALaHWsbrOZ4SKvLyZgjCWM7AQADAgADeQADOwQ"
    },
    "New Balance": {
        "male": "AgACAgIAAxkBAAICQWoPEVILsueVeW25EkMvu39zelW5AAKhHWsbrOZ4SG2Cs3_WbxXBAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICX2oPFVQoQy3z4_lY1X-5mTC0LafNAALDHWsbrOZ4SMVuehD8oERKAQADAgADeQADOwQ"
    },
    "Nike": {
        "male": "AgACAgIAAxkBAAICOWoPECpqsQ8YZ8h0Q6i1JccTgHbEAAKRHWsbrOZ4SLjMPVaW8xzUAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICWWoPFIiLJo9FpzGW9ukZ8NYaEHM6AAK1HWsbrOZ4SHbqqU1mlfCLAQADAgADeQADOwQ"
    },
    "Palladium": {
        "male": "AgACAgIAAxkBAAICVWoPE98tYS5esugbkzvAvlP-aJj1AAKxHWsbrOZ4SK-zZJa1tmtjAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICb2oPF3ZMFMHdn63vMPMmo1KGmI3PAALgHWsbrOZ4SBMWSirqWAi_AQADAgADeQADOwQ"
    },
    "Puma": {
        "male": "AgACAgIAAxkBAAICQ2oPEZzNMSQX7E_A_vVywjEFp2VXAAKjHWsbrOZ4SD-1wyw0QrIMAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICYWoPFZXttOQVI_f8q2RnrhpcM3dGAALEHWsbrOZ4SLORiXo3zxm9AQADAgADeQADOwQ"
    },
    "Reebok": {
        "male": "AgACAgIAAxkBAAICRWoPEeqE6qpVw00KOD5ziMVRyYJTAAKkHWsbrOZ4SLhtiy6o8yilAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICY2oPFc-HbUM3GkHZBJHhsVC4jV5xAALFHWsbrOZ4SKpn6MgBTLwJAQADAgADeQADOwQ"
    },
    "Salomon": {
        "male": "AgACAgIAAxkBAAICR2oPEinvtgaFPZM2hTGDwcVDjmcHAAKmHWsbrOZ4SELuZgnNePyoAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICZWoPFgouQ_7J98DR8Hix0p7Z3DMEAALGHWsbrOZ4SK5GFYpskxJRAQADAgADeQADOwQ"
    },
    "STREETBEAT": {
        "male": "AgACAgIAAxkBAAICO2oPEIndzlvZngeVIVR8Oyl5qn07AAKWHWsbrOZ4SLCesXsLZLutAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICW2oPFM2TJVCH8m2mirkXezQZSpoUAAK2HWsbrOZ4SOqMY0gj3AFGAQADAgADeQADOwQ"
    },
    "Timberland": {
        "male": "AgACAgIAAxkBAAICS2oPEp2BTwx9yR6KsCTAnaJATcpUAAKoHWsbrOZ4SPmRMq7aQRxyAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICaWoPFpsTAZmV4SceO6RdFG_rmmg5AALXHWsbrOZ4SMSdHgTclowgAQADAgADeQADOwQ"
    },
    "Vans": {
        "male": "AgACAgIAAxkBAAICM2oPDjEJkklWS7m-ZBqy_jfy5rPKAAKZGWsbw2V5SBZXyBK6bjrzAQADAgADeQADOwQ",
        "female": "AgACAgIAAxkBAAICV2oPFCejAAHSdMI2723bdD2r3XMzJAACtB1rG6zmeEgdnIjs2IOWqgEAAwIAA3kAAzsE"
    }
}

user_brand_choice = {}


def brands_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for brand in BRANDS:
        buttons.append(types.InlineKeyboardButton(brand, callback_data=f"brand_{brand}"))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"))
    return markup


def gender_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("👨 Мужской", callback_data="gender_male"),
        types.InlineKeyboardButton("👩 Женский", callback_data="gender_female")
    )
    markup.add(types.InlineKeyboardButton("◀️ Назад к брендам", callback_data="back_to_brands"))
    return markup


# -------------------------------------------------------------------
# Функция для случайного выбора менеджера (рандомное распределение)
# -------------------------------------------------------------------
def get_random_manager():
    """Возвращает случайного менеджера из списка MANAGER_IDS"""
    if not MANAGER_IDS:
        return None
    return random.choice(MANAGER_IDS)


def get_free_manager():
    """Находит свободного менеджера или случайного, если все заняты"""
    active = load_active()

    # Ищем свободного менеджера (у которого нет активных диалогов)
    for manager_id in MANAGER_IDS:
        if not any(a == str(manager_id) for a in active.values()):
            return manager_id

    # Если все заняты — возвращаем случайного
    return get_random_manager()


# -------------------------------------------------------------------
# КОМАНДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# -------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id in MANAGER_IDS:
        bot.send_message(
            message.chat.id,
            "👨‍💼 Панель менеджера\n\n"
            "Вам будут приходить сообщения от пользователей.\n"
            "Используйте кнопки для управления.",
            reply_markup=manager_keyboard()
        )
        return

    users = load_users()
    if str(message.chat.id) not in users:
        users[str(message.chat.id)] = {
            "name": message.from_user.first_name,
            "username": message.from_user.username,
            "first_seen": str(message.date)
        }
        save_users(users)

    bot.send_message(
        message.chat.id,
        f"👟 Привет, {message.from_user.first_name}! 😊\n\n"
        f"Добро пожаловать в Street Beat!\n\n"
        f"🛍️ Нажмите «Магазин» для перехода в каталог\n"
        f"❓ Или нажмите «Связаться с поддержкой» для связи с оператором",
        reply_markup=user_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "🛍️ Магазин" and message.chat.id not in MANAGER_IDS)
def shop(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "🛍️ Открыть магазин Street Beat",
        web_app=types.WebAppInfo(url="https://street-beat.ru")
    )
    markup.add(btn)
    bot.send_message(
        message.chat.id,
        "🛍️ Добро пожаловать в Street Beat!\n\n"
        "Нажмите на кнопку ниже, чтобы открыть наш каталог кроссовок и кед.\n\n"
        "👟 Удобный каталог, фото, цены и корзина — всё внутри!",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "❓ Помощь" and message.chat.id not in MANAGER_IDS)
def help_user(message):
    help_text = (
        "👟 Street Beat — помощь\n\n"
        "📋 Что я умею:\n"
        "• 🛍️ Магазин — каталог кроссовок и кед\n"
        "• 🚚 Доставка — сроки и стоимость\n"
        "• 💳 Оплата и возврат — способы оплаты и условия возврата\n"
        "• 📏 Таблица размеров — подбор размера по брендам\n"
        "• 📞 Контакты — как с нами связаться\n"
        "• 👤 Поддержка — связаться с оператором\n\n"
        "❓ Есть вопрос? Нажмите «Связаться с поддержкой»!"
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: message.text == "🚚 Доставка" and message.chat.id not in MANAGER_IDS)
def delivery(message):
    delivery_text = (
        "🚚 *Способы доставки*\n\n"
        "🚚 Курьерская доставка до двери\n"
        "⏰ Срок: завтра или позднее\n"
        "💰 Стоимость: от 799 руб.\n\n"
        "⚡ Доставка в день заказа\n"
        "⏰ Срок: сегодня\n"
        "💰 Стоимость: 1199 руб. (в пределах МКАД)\n\n"
        "🏪 Получить в магазине\n"
        "📍 Самовывоз из магазинов в Москве\n"
        "✅ Готовность: через 30 минут\n\n"
        "📦 Логистическая компания 5Post\n"
        "📍 Постаматы и пункты выдачи\n\n"
        "📮 Яндекс Доставка\n"
        "📍 Постаматы и ПВЗ Яндекс.Маркет"
    )
    bot.send_message(message.chat.id, delivery_text)


@bot.message_handler(func=lambda message: message.text == "💳 Оплата и возврат" and message.chat.id not in MANAGER_IDS)
def payment_and_return(message):
    text = (
        "💳 *Оплата*\n\n"
        "💻 Онлайн-оплата\n"
        "Оплата на сайте и в мобильном приложении через сервис ЮKassa.\n"
        "Международный стандарт безопасности PCI DSS.\n"
        "Оплатить можно:\n"
        "   💳 банковской картой (Visa, MasterCard, MIR, JCB)\n"
        "   🏦 через интернет-банк (Сбер Онлайн, Альфа-Клик, Тинькофф)\n\n"
        "📱 Долями\n"
        "Оплата частями: 25% каждые две недели.\n"
        "Сумма: от 1 000 ₽ до 50 000 ₽.\n\n"
        "📦 При получении\n"
        "   💵 наличными\n"
        "   💳 банковской картой\n\n"
        "🎁 Подарочными картами Street Beat\n"
        "Оплата до 100% покупки в магазине или на сайте.\n\n"
        "──────────────────\n\n"
        "🔄 *Возврат*\n\n"
        "• Обмен или возврат в течение 14 дней\n"
        "• Товар должен быть в идеальном состоянии\n"
        "• Сохраните чек и упаковку\n"
        "• Бесплатный возврат при браке в течение 2 лет\n\n"
        "📞 Для консультации нажмите «Связаться с поддержкой»"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "📞 Контакты" and message.chat.id not in MANAGER_IDS)
def contacts(message):
    contacts_text = (
        "📞 Наши контакты\n\n"
        "📱 Телефон: 8 (800) 700-82-60\n"
        "🕐 Работаем: 10:00 - 22:00 (МСК)\n\n"
        "💬 Или нажмите «Связаться с поддержкой»"
    )
    bot.send_message(message.chat.id, contacts_text)


@bot.message_handler(func=lambda message: message.text == "📏 Таблица размеров" and message.chat.id not in MANAGER_IDS)
def size_table_start(message):
    bot.send_message(
        message.chat.id,
        "📏 *Таблица размеров кроссовок*\n\n"
        "Выберите бренд, чтобы узнать соответствие размеров:",
        parse_mode='Markdown',
        reply_markup=brands_keyboard()
    )


# -------------------------------------------------------------------
# ОБРАБОТЧИК ВЫБОРА ТИПА ВОПРОСА
# -------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text in QUESTION_TYPES.keys() and message.chat.id not in MANAGER_IDS)
def handle_question_type(message):
    """Обработка выбора типа вопроса"""
    user_id = message.chat.id
    selected_type = message.text

    # Сохраняем выбранный тип вопроса
    user_question_type[user_id] = selected_type

    # Отправляем подтверждение
    bot.send_message(
        user_id,
        f"✅ Вы выбрали тип вопроса: *{selected_type}*\n\n"
        f"📝 Теперь напишите подробности вашего вопроса.\n"
        f"Оператор ответит в ближайшее время.",
        parse_mode='Markdown'
    )


# -------------------------------------------------------------------
# ОБРАБОТКА СООБЩЕНИЙ ОТ ПОЛЬЗОВАТЕЛЕЙ ПОСЛЕ ВЫБОРА ТИПА ВОПРОСА
# -------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.id not in MANAGER_IDS and message.text not in [
    "🛍️ Магазин", "❓ Помощь", "🚚 Доставка", "💳 Оплата и возврат",
    "📏 Таблица размеров", "📞 Контакты", "👤 Связаться с поддержкой", "❌ Завершить диалог",
    "◀️ Отмена"
] + list(QUESTION_TYPES.keys()))
def handle_question_details(message):
    """Обработка деталей вопроса после выбора типа"""
    user_id = message.chat.id
    user_id_str = str(user_id)

    # Проверяем, есть ли у пользователя выбранный тип вопроса
    if user_id not in user_question_type:
        # Если нет, отправляем к выбору типа
        bot.send_message(
            message.chat.id,
            "❓ Пожалуйста, сначала выберите тип вопроса:\n\n"
            "Нажмите «Связаться с поддержкой» и выберите тему.",
            reply_markup=user_keyboard()
        )
        return

    # Проверяем, не в активном ли уже диалоге
    active = load_active()
    if user_id_str in active:
        # Если уже в диалоге, пересылаем как обычно
        manager_id = int(active[user_id_str])
        question_type = user_question_type.get(user_id, "Не выбран")

        bot.send_message(
            manager_id,
            f"📩 *Сообщение от пользователя*\n\n"
            f"👤 {message.from_user.first_name}\n"
            f"🆔 ID: `{message.chat.id}`\n"
            f"📋 Тип вопроса: *{question_type}*\n\n"
            f"📝 {message.text}",
            parse_mode='Markdown'
        )

        # Очищаем тип вопроса
        del user_question_type[user_id]

        bot.send_message(
            message.chat.id,
            "✉️ Сообщение отправлено оператору. Ожидайте ответ..."
        )
        return

    # Ищем свободного менеджера
    manager_id = get_free_manager()

    question_type = user_question_type.get(user_id, "Не выбран")

    if manager_id:
        # Создаём активный диалог
        active[user_id_str] = str(manager_id)
        save_active(active)

        # Уведомляем менеджера с типом вопроса
        bot.send_message(
            manager_id,
            f"🟢 *Новый запрос в поддержку!*\n\n"
            f"👤 Пользователь: {message.from_user.first_name}\n"
            f"🆔 ID: `{message.chat.id}`\n"
            f"📋 Тип вопроса: *{question_type}*\n\n"
            f"📝 {message.text}\n\n"
            f"Для ответа просто напишите сообщение в этот чат.",
            parse_mode='Markdown'
        )

        # Очищаем тип вопроса
        del user_question_type[user_id]

        bot.send_message(
            message.chat.id,
            "👤 *Вы подключены к оператору* ✅\n\n"
            "Ваше сообщение получено. Оператор ответит в ближайшее время.\n\n"
            "Чтобы закончить диалог, нажмите «❌ Завершить диалог»",
            parse_mode='Markdown',
            reply_markup=support_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "😔 Все операторы сейчас заняты.\n"
            "Пожалуйста, подождите или напишите позже."
        )


@bot.message_handler(
    func=lambda message: message.text == "👤 Связаться с поддержкой" and message.chat.id not in MANAGER_IDS)
def connect_support(message):
    active = load_active()
    user_id = str(message.chat.id)

    if user_id in active:
        bot.send_message(
            message.chat.id,
            "✅ Вы уже на связи с оператором. Напишите ваш вопрос."
        )
        return

    # Показываем панельку с типами вопросов
    bot.send_message(
        message.chat.id,
        "🆘 *Чем мы можем вам помочь?*\n\n"
        "Пожалуйста, выберите тему вашего вопроса:",
        parse_mode='Markdown',
        reply_markup=question_type_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == "❌ Завершить диалог" and message.chat.id not in MANAGER_IDS)
def end_support(message):
    active = load_active()
    user_id = str(message.chat.id)

    if user_id in active:
        manager_id = int(active[user_id])
        del active[user_id]
        save_active(active)

        bot.send_message(
            manager_id,
            f"🔴 Диалог завершён\n\n"
            f"Пользователь {message.from_user.first_name} завершил общение."
        )

        bot.send_message(
            message.chat.id,
            "👋 Диалог с оператором завершён.\n\n"
            "Хорошего дня! 😊",
            reply_markup=user_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "У вас нет активного диалога с оператором.")


# -------------------------------------------------------------------
# ОБРАБОТКА КНОПКИ "◀️ Отмена"
# -------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "◀️ Отмена" and message.chat.id not in MANAGER_IDS)
def cancel_question(message):
    """Отмена выбора типа вопроса"""
    user_id = message.chat.id
    if user_id in user_question_type:
        del user_question_type[user_id]

    bot.send_message(
        message.chat.id,
        "❌ Вы отменили обращение в поддержку.\n\n"
        "Если передумаете — нажмите «Связаться с поддержкой» снова.",
        reply_markup=user_keyboard()
    )


# -------------------------------------------------------------------
# Callback-запросы для таблицы размеров
# -------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('brand_'))
def brand_selected(call):
    brand = call.data.replace('brand_', '')
    user_brand_choice[call.message.chat.id] = brand
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(
        call.message.chat.id,
        f"📏 *Таблица размеров {brand}*\n\nВыберите пол:",
        parse_mode='Markdown',
        reply_markup=gender_keyboard()
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def gender_selected(call):
    gender = call.data.replace('gender_', '')
    user_id = call.message.chat.id
    brand = user_brand_choice.get(user_id)

    if not brand:
        bot.send_message(
            user_id,
            "❌ Что-то пошло не так. Пожалуйста, начните заново с кнопки «📏 Таблица размеров»"
        )
        bot.answer_callback_query(call.id)
        return

    size_id = SIZE_TABLES.get(brand, {}).get(gender)
    gender_text = "мужской" if gender == "male" else "женский"

    if size_id:
        try:
            bot.send_photo(
                user_id,
                size_id,
                caption=f"📏 *Таблица размеров {brand} ({gender_text})*\n\n"
                        f"Как определить свой размер:\n"
                        f"1️⃣ Измерьте длину стопы в см\n"
                        f"2️⃣ Найдите соответствующее значение в таблице\n"
                        f"3️⃣ При заказе ориентируйтесь на этот размер\n\n"
                        f"❓ Остались вопросы? Нажмите «Связаться с поддержкой»",
                parse_mode='Markdown'
            )
        except Exception as e:
            bot.send_message(
                user_id,
                f"📏 *Таблица размеров {brand} ({gender_text})*\n\n"
                f"К сожалению, изображение временно недоступно.\n"
                f"Пожалуйста, напишите нам в поддержку, и мы поможем подобрать размер! 😊",
                parse_mode='Markdown'
            )
    else:
        bot.send_message(
            user_id,
            f"❌ Таблица размеров для бренда {brand} временно недоступна.\n"
            f"Пожалуйста, напишите в поддержку, и мы поможем! 😊"
        )

    if user_id in user_brand_choice:
        del user_brand_choice[user_id]
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_brands")
def back_to_brands(call):
    user_id = call.message.chat.id
    if user_id in user_brand_choice:
        del user_brand_choice[user_id]
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    bot.send_message(
        user_id,
        "📏 *Таблица размеров кроссовок*\n\nВыберите бренд:",
        parse_mode='Markdown',
        reply_markup=brands_keyboard()
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    user_id = call.message.chat.id
    if user_id in user_brand_choice:
        del user_brand_choice[user_id]
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    bot.send_message(
        user_id,
        "👟 Возвращаем вас в главное меню!\nЧем могу помочь ещё? 😊",
        reply_markup=user_keyboard()
    )
    bot.answer_callback_query(call.id)


# -------------------------------------------------------------------
# ОБРАБОТКА СООБЩЕНИЙ ОТ ПОЛЬЗОВАТЕЛЕЙ (пересылка менеджеру)
# -------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.id not in MANAGER_IDS and message.text not in [
    "🛍️ Магазин", "❓ Помощь", "🚚 Доставка", "💳 Оплата и возврат",
    "📏 Таблица размеров", "📞 Контакты", "👤 Связаться с поддержкой", "❌ Завершить диалог",
    "◀️ Отмена"
] + list(QUESTION_TYPES.keys()))
def forward_to_manager(message):
    active = load_active()
    user_id = str(message.chat.id)

    if user_id in active:
        manager_id = int(active[user_id])
        bot.send_message(
            manager_id,
            f"📩 Сообщение от пользователя\n\n"
            f"👤 {message.from_user.first_name}\n"
            f"🆔 ID: {message.chat.id}\n\n"
            f"📝 {message.text}"
        )
        bot.send_message(
            message.chat.id,
            "✉️ Сообщение отправлено оператору. Ожидайте ответ..."
        )
    else:
        bot.send_message(
            message.chat.id,
            "❓ Сначала нажмите «Связаться с поддержкой»"
        )

# -------------------------------------------------------------------
# ВРЕМЕННАЯ КОМАНДА ДЛЯ ПОЛУЧЕНИЯ FILE_ID (потом можно удалить)
# -------------------------------------------------------------------
@bot.message_handler(content_types=['photo'])
def get_file_id_from_my_bot(message):
    if message.chat.id not in MANAGER_IDS:
        bot.reply_to(message, "❌ Отправлять фото может только менеджер")
        return
    file_id = message.photo[-1].file_id
    bot.reply_to(
        message,
        f"✅ file_id получен!\n\n{file_id}\n\nЭтот ID можно вставить в словарь SIZE_TABLES для бренда."
    )


# -------------------------------------------------------------------
# КОМАНДЫ ДЛЯ МЕНЕДЖЕРА
# -------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.id in MANAGER_IDS and message.text == "📋 Активные чаты")
def show_active_chats(message):
    active = load_active()
    users = load_users()
    if not active:
        bot.send_message(message.chat.id, "📭 Нет активных диалогов.")
        return
    text = "📋 Активные диалоги:\n\n"
    for user_id, manager_id in active.items():
        user_info = users.get(user_id, {})
        name = user_info.get('name', 'Неизвестно')
        text += f"• {user_id} — {name}\n"
    text += "\nЧтобы ответить, просто напишите сообщение — оно уйдёт пользователю.\n\n"
    text += "Или используйте:\n/reply 123456789 Ваш ответ"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda message: message.chat.id in MANAGER_IDS and message.text == "📊 Статистика")
def show_stats(message):
    users = load_users()
    active = load_active()
    text = (
        f"📊 Статистика бота\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"💬 Активных диалогов: {len(active)}\n"
        f"👨‍💼 Менеджеров: {len(MANAGER_IDS)}"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda message: message.chat.id in MANAGER_IDS and message.text == "⚙️ Помощь")
def manager_help(message):
    help_text = (
        "👨‍💼 Помощь менеджеру\n\n"
        "📌 Как отвечать пользователям:\n"
        "• Просто напишите сообщение — оно уйдёт активному пользователю\n"
        "• Или используйте: /reply 123456789 Ваш ответ\n\n"
        "📌 Команды:\n"
        "• /users — список всех пользователей\n"
        "• /active — активные диалоги\n"
        "• /reply ID текст — ответить конкретному пользователю\n"
        "• /end ID — завершить диалог с пользователем\n\n"
        "📌 Кнопки:\n"
        "• «📋 Активные чаты» — список текущих диалогов\n"
        "• «📊 Статистика» — общая информация"
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['reply'])
def reply_to_user(message):
    if message.chat.id not in MANAGER_IDS:
        return
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            "❌ Используйте: /reply ID_пользователя Текст ответа\n\n"
            "Пример: /reply 123456789 Здравствуйте!"
        )
        return
    try:
        user_id = int(parts[1])
        answer = parts[2]
        bot.send_message(user_id, f"👤 Ответ оператора:\n\n{answer}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['end'])
def end_conversation(message):
    if message.chat.id not in MANAGER_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Используйте: /end ID_пользователя")
        return
    try:
        user_id = parts[1]
        active = load_active()
        if user_id in active:
            del active[user_id]
            save_active(active)
            bot.send_message(int(user_id), "👋 Оператор завершил диалог. Хорошего дня! 😊", reply_markup=user_keyboard())
            bot.send_message(message.chat.id, f"✅ Диалог с {user_id} завершён")
        else:
            bot.send_message(message.chat.id, f"❌ Активный диалог с {user_id} не найден")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка при завершении диалога")


@bot.message_handler(commands=['active'])
def active_chats_command(message):
    if message.chat.id not in MANAGER_IDS:
        return
    active = load_active()
    if not active:
        bot.send_message(message.chat.id, "📭 Нет активных диалогов.")
        return
    text = "📋 Активные диалоги:\n\n"
    for user_id, manager_id in active.items():
        text += f"• {user_id}\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['users'])
def all_users_command(message):
    if message.chat.id not in MANAGER_IDS:
        return
    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "📭 Нет пользователей.")
        return
    text = "👥 Все пользователи:\n\n"
    for user_id, info in list(users.items())[:20]:
        text += f"• {user_id} — {info.get('name', '?')}\n"
    if len(users) > 20:
        text += f"\n...и ещё {len(users) - 20} пользователей"
    bot.send_message(message.chat.id, text)


@bot.message_handler(
    func=lambda message: message.chat.id in MANAGER_IDS and message.text and not message.text.startswith(
        '/') and message.text not in [
                             "📋 Активные чаты", "📊 Статистика", "⚙️ Помощь"
                         ])
def manager_reply(message):
    active = load_active()
    user_id = None
    for uid, mid in active.items():
        if int(mid) == message.chat.id:
            user_id = int(uid)
            break
    if user_id:
        bot.send_message(user_id, f"👤 Ответ оператора:\n\n{message.text}")
        bot.send_message(message.chat.id, f"✅ Ответ отправлен пользователю {user_id}")
    else:
        bot.send_message(
            message.chat.id,
            "❌ Нет активного диалога.\n\n"
            "Сначала дождитесь сообщения от пользователя или используйте:\n"
            "/reply ID Текст для ответа конкретному пользователю"
        )


@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.send_message(message.chat.id, f"Ваш ID: {message.chat.id}")


# -------------------------------------------------------------------
# ЗАПУСК БОТА
# -------------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    print('Бот поддержки Street Beat запущен! 🚀')
    print(f'Менеджеры: {MANAGER_IDS}')
    print('Сайт магазина: https://street-beat.ru')
    print('Пинг запущен (каждые 10 минут)')
    bot.infinity_polling(timeout=60)