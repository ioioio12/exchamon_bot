import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from data import CURRENCIES, CRYPTOCURRENCIES, ALL_CURRENCIES
from keyboards import (
    get_main_menu,
    get_currency_keyboard,
    get_base_currency_keyboard,
    get_back_to_menu_keyboard,
    get_quick_conversion_keyboard,
    get_crypto_menu_keyboard,
    get_news_menu_keyboard,
    get_top_crypto_keyboard,
    get_currency_type_keyboard
)
from services import CurrencyConverter
from news_service import NewsService
import os
from aiogram.types import FSInputFile



# Словарь соответствия фотографий и действий
PHOTOS = {
    # Главное меню и приветствие
    "welcome": "Group 1.png",  # "Добро пожаловать!"

    # Конвертация валют
    "select_currency_type": "Group 1 (1).png",  # "Выберите тип валют для конвертации"
    "select_base_currency": "Group 1 (2).png",  # "Выберите исходную валюту"
    "select_target_currency": "Group 1 (3).png",  # "Выберите целевую валюту"
    "enter_amount": "Group 1 (4).png",  # "Введите сумму для конвертации"
    "conversion_result": "Group 1 (5).png",  # "Результат конвертации"

    # Курсы валют
    "currency_rates": "Group 1 (6).png",  # "Курсы к вашей валюте"
    "select_base_display": "Group 1 (8).png",  # "Выберите основную валюту для отображения курсов"
    "base_currency_changed": "Group 1 (7).png",  # "Основная валюта изменена"

    # Криптовалюты
    "crypto_market": "Group 1 (9).png",  # "Криптовалютный рынок"
    "crypto_rates": "Group 1 (10).png",  # "Курс криптовалюты"
    "top_crypto": "Group 1 (21).png",  # "Топ-10 криптовалют"

    # Новости
    "news_menu": "Group 1 (11).png",  # "Выберите категорию новостей"
    "crypto_news": "Group 1 (13).png",  # "Криптовалютные новости"
    "financial_news": "Group 1 (12).png",  # "Финансовые новости"
    "latest_news": "Group 1 (19).png",  # "Последние Финансовые новости"
    "economy_news": "Group 1 (14).png",  # "Экономические новости"
    "banking_news": "Group 1 (15).png",  # "Новости банковского сектора"
    "russia_news": "Group 1 (16).png",  # "РФ Все новости"
    "news_search": "Group 1 (18).png",  # "Поиск новостей"

    # Помощь
    "help": "Group 1 (20).png",  # "Помощь по использованию бота"
}




# В начале файла, после user_data
user_messages: Dict[int, List[int]] = {}

def ensure_user_data(user_id: int) -> dict:
    """Создаёт запись пользователя, если её нет"""
    if user_id not in user_data:
        user_data[user_id] = {
            'base_currency': 'RUB',  # или 'USD' — как тебе удобнее
            'conversion_history': []
        }
    return user_data[user_id]

# Функция для сохранения ID сообщения
def save_message_id(user_id: int, message_id: int):
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(message_id)

async def safe_edit_caption(callback_or_message, text: str, reply_markup=None):
    """Безопасное редактирование caption у фото — не падает никогда"""
    try:
        if hasattr(callback_or_message, "message"):
            msg = callback_or_message.message
        else:
            msg = callback_or_message

        await msg.edit_caption(
            caption=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        if "there is no text" in str(e) or "message can't be edited" in str(e):
            # Если не удалось — просто отправляем новое
            try:
                await msg.delete()
            except:
                pass
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile("photos/Group 1.png"),  # fallback фото
                caption=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            print(f"Ошибка edit_caption: {e}")

async def delete_last_bot_message(user_id: int):
    """Удаляет последнее сообщение бота у пользователя"""
    if user_id in user_messages and user_messages[user_id]:
        try:
            last_msg_id = user_messages[user_id][-1]
            await bot.delete_message(user_id, last_msg_id)
            user_messages[user_id].pop()
        except:
            pass

# Функция для удаления предыдущих сообщений
async def delete_previous_messages(user_id: int, keep_last: int = 1):
    """Удаляет все предыдущие сообщения пользователя, оставляя только keep_last последних"""
    if user_id in user_messages and len(user_messages[user_id]) > keep_last:
        messages_to_delete = user_messages[user_id][:-keep_last]

        # Удаляем сообщения
        for msg_id in messages_to_delete:
            try:
                await bot.delete_message(user_id, msg_id)
            except:
                pass  # Игнорируем ошибки при удалении

        # Оставляем только последние сообщения
        user_messages[user_id] = user_messages[user_id][-keep_last:]


async def send_photo(message, photo_key, caption="", reply_markup=None, parse_mode=None, **kwargs):
    """Отправляет фотографию по ключу из словаря PHOTOS"""
    try:
        photo_path = f"photos/{PHOTOS.get(photo_key, 'Group 1.png')}"
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            sent_message = await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                **kwargs
            )
            # Сохраняем ID сообщения
            save_message_id(message.from_user.id, sent_message.message_id)
            return True, sent_message
        else:
            print(f"Файл {photo_path} не найден")
            # Отправляем просто текст, если фото не найдено
            sent_message = await message.answer(
                caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                **kwargs
            )
            save_message_id(message.from_user.id, sent_message.message_id)
            return False, sent_message
    except Exception as e:
        print(f"Ошибка при отправке фотографии {photo_key}: {e}")
        # Fallback на текстовое сообщение
        sent_message = await message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs
        )
        save_message_id(message.from_user.id, sent_message.message_id)
        return False, sent_message


# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
converter = CurrencyConverter()
news_service = NewsService()


# Состояния FSM
class ConverterStates(StatesGroup):
    select_base = State()
    select_target = State()
    enter_amount = State()
    set_base_currency = State()
    select_currency_type = State()
    enter_news_search = State()


# Хранение пользовательских данных (временное решение)
user_data: Dict[int, Dict[str, Any]] = {}


# Команда /start
# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # Очищаем все предыдущие сообщения пользователя
    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                await bot.delete_message(user_id, msg_id)
            except:
                pass
        user_messages[user_id] = []

    # Инициализация данных пользователя
    user_data[user_id] = {
        'base_currency': 'RUB',
        'conversion_history': []
    }

    base_currency = ensure_user_data(user_id)['base_currency']

    welcome_text = (
        "💱 *Конвертер валют*\n\n"
        "Я помогу вам конвертировать валюты по актуальному курсу.\n\n"
        "Используйте кнопки ниже для работы с ботом:"
    )

    # Удаляем команду /start
    try:
        await message.delete()
    except:
        pass

    # Отправляем фотографию
    await send_photo(message, "welcome", welcome_text, get_main_menu(), "Markdown")



# Главное меню
@dp.message(F.text == "💱 Конвертировать валюту")
async def convert_currency(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Удаляем предыдущие сообщения (оставляем только последнее)
    await delete_previous_messages(user_id, keep_last=0)

    # Удаляем само сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    await send_photo(
        message,
        "select_currency_type",
        "",
        get_currency_type_keyboard()
    )
    await state.set_state(ConverterStates.select_currency_type)


@dp.message(F.text == "📊 Курсы валют")
async def show_rates(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    base_currency = user_data.get(user_id, {}).get('base_currency', 'RUB')

    await delete_previous_messages(user_id, keep_last=0)

    # Удаляем само сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    loading_msg = await message.answer("🔄 Загружаю актуальные курсы...")

    try:
        # Получаем курсы ОТНОСИТЕЛЬНО базовой валюты
        rates = await converter.get_all_rates(base_currency)
        if not rates:
            await loading_msg.edit_text("❌ Не удалось получить курсы валют. Попробуйте позже.")
            return

        rates_text = f"📈 *Курсы к {base_currency}:*\n\n"

        # Список валют для отображения (все популярные, кроме базовой)
        currencies_to_show = [
            ('🇷🇺', 'RUB'),
            ('🇺🇸', 'USD'),
            ('🇪🇺', 'EUR'),
            ('🇬🇧', 'GBP'),
            ('🇯🇵', 'JPY'),
            ('🇨🇳', 'CNY'),
            ('🇨🇭', 'CHF'),
            ('🇨🇦', 'CAD'),
            ('🇹🇷', 'TRY'),
            ('🇰🇿', 'KZT'),
            ('🇺🇦', 'UAH'),
            ('🇧🇾', 'BYN'),
            ('🇦🇪', 'AED')
        ]

        # Фильтруем - оставляем только те, которые не являются базовой валютой
        currencies_to_show = [(emoji, code) for emoji, code in currencies_to_show if code != base_currency]

        for emoji, target_currency in currencies_to_show[:10]:  # Показываем первые 10
            # Получаем курс из base_currency в target_currency
            rate_from_base_to_target = await converter.get_exchange_rate(base_currency, target_currency)

            if rate_from_base_to_target:
                # Вычисляем обратный курс: 1 target_currency = ? base_currency
                reverse_rate = 1 / rate_from_base_to_target

                # Форматируем в зависимости от величины
                if reverse_rate < 0.01:
                    formatted_rate = f"{reverse_rate:.6f}"
                elif reverse_rate < 1:
                    formatted_rate = f"{reverse_rate:.4f}"
                elif reverse_rate < 10:
                    formatted_rate = f"{reverse_rate:.3f}"
                elif reverse_rate < 100:
                    formatted_rate = f"{reverse_rate:.2f}"
                elif reverse_rate < 1000:
                    formatted_rate = f"{reverse_rate:.1f}"
                else:
                    formatted_rate = f"{reverse_rate:.0f}"

                rates_text += f"{emoji} 1 {target_currency} = {formatted_rate} {base_currency}\n"

        rates_text += f"\n📅 *Обновлено:* {datetime.now().strftime('%d.%m.%Y %H:%M')}"

        # Удаляем сообщение о загрузке
        await loading_msg.delete()

        # Отправляем фото С подписью (текстом курсов)
        await send_photo(
            message,
            "currency_rates",
            rates_text,  # передаем текст как caption
            parse_mode="Markdown"  # добавляем parse_mode
        )

    except Exception as e:
        print(f"Ошибка: {e}")
        await loading_msg.edit_text("❌ Ошибка при загрузке курсов")

@dp.message(F.text == "⚙️ Выбрать основную валюту")
async def set_base_currency(message: types.Message, state: FSMContext):
    sent = await send_photo(
        message,
        "select_base_display",
        "Выберите основную валюту для отображения курсов:",
        get_base_currency_keyboard()
    )

    if not sent:
        await message.answer(
            "Выберите основную валюту для отображения курсов:",
            reply_markup=get_base_currency_keyboard()
        )
    await state.set_state(ConverterStates.set_base_currency)


@dp.message(F.text == "ℹ️ Помощь")
async def show_help(message: types.Message):
    help_text = (
        "📖 *Помощь по использованию бота*\n\n"
        "💱 *Конвертировать валюту* - конвертация суммы из одной валюты в другую\n\n"
        "📊 *Курсы валют* - просмотр актуальных курсов популярных валют\n\n"
        "₿ *Криптовалюты* - курсы криптовалют и конвертация\n\n"
        "📰 *Новости* - финансовые и криптоновости\n\n"
        "⚙️ *Выбрать основную валюту* - установить базовую валюту для отображения курсов\n\n"
        "🔄 *Доступные валюты:*\n"
        "• Фиатные: USD, EUR, RUB, GBP, JPY и др.\n"
        "• Криптовалюты: BTC, ETH, BNB, XRP, SOL и др.\n\n"
        "💡 *Совет:* Для быстрой конвертации используйте команду /convert"
    )

    sent = await send_photo(
        message,
        "help",
        help_text,
        parse_mode="Markdown"
    )

    if not sent:
        await message.answer(help_text, parse_mode="Markdown")


# Новый хендлер для выбора типа валюты
# Новый хендлер для выбора типа валюты
@dp.callback_query(F.data.startswith("currency_type:"))
async def process_currency_type(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    currency_type = callback.data.split(":")[1]

    await state.update_data(currency_type=currency_type)

    # Удаляем предыдущие сообщения
    await delete_previous_messages(user_id, keep_last=0)

    # Отправляем фотографию для выбора исходной валюты
    await send_photo(
        callback.message,
        "select_base_currency",
        "Выберите исходную валюту:",
        get_currency_keyboard(None, "select_base", 0, currency_type)
    )

    await state.set_state(ConverterStates.select_base)
    await callback.answer()


# Обновляем хендлер выбора базовой валюты для работы с типами
@dp.callback_query(F.data.startswith("select_base:"))
async def process_base_currency(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    currency = data_parts[1]
    page = int(data_parts[2]) if len(data_parts) > 2 else 0
    currency_type = data_parts[3] if len(data_parts) > 3 else "all"

    # Получаем название валюты
    currency_name = ALL_CURRENCIES.get(currency, currency)
    await state.update_data(base_currency=currency, currency_type=currency_type)

    # Удаляем предыдущее сообщение
    await callback.message.delete()

    # Отправляем фотографию для выбора целевой валюты
    sent = await send_photo(
        callback.message,
        "select_target_currency",
        f"✅ Выбрана исходная валюта: {currency_name}\n\nТеперь выберите целевую валюту:",
        get_currency_keyboard(None, "select_target", page, currency_type)
    )

    if not sent:
        await callback.message.answer(
            f"✅ Выбрана исходная валюта: {currency_name}\n\n"
            f"Теперь выберите целевую валюту:",
            reply_markup=get_currency_keyboard(None, "select_target", page, currency_type)
        )

    await state.set_state(ConverterStates.select_target)
    await callback.answer()


# Обновляем хендлер выбора целевой валюты
@dp.callback_query(F.data.startswith("select_target:"))
async def process_target_currency(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split(":")
    target_currency = data_parts[1]
    page = int(data_parts[2]) if len(data_parts) > 2 else 0
    currency_type = data_parts[3] if len(data_parts) > 3 else "all"

    data = await state.get_data()
    base_currency = data.get('base_currency')

    if base_currency == target_currency:
        await callback.answer("❌ Исходная и целевая валюты не могут совпадать!")
        return

    await state.update_data(target_currency=target_currency)

    # Получаем названия валют
    base_name = ALL_CURRENCIES.get(base_currency, base_currency)
    target_name = ALL_CURRENCIES.get(target_currency, target_currency)

    # Удаляем предыдущее сообщение
    await callback.message.delete()

    # Отправляем фотографию для ввода суммы
    sent = await send_photo(
        callback.message,
        "enter_amount",
        f"💱 *Конвертация:*\n"
        f"Из: {base_name}\n"
        f"В: {target_name}\n\n"
        f"Введите сумму для конвертации в {base_currency}:",
        parse_mode="Markdown"
    )

    if not sent:
        await callback.message.answer(
            f"💱 *Конвертация:*\n"
            f"Из: {base_name}\n"
            f"В: {target_name}\n\n"
            f"Введите сумму для конвертации в {base_currency}:",
            parse_mode="Markdown"
        )

    await state.set_state(ConverterStates.enter_amount)
    await callback.answer()


# Обновляем хендлер пагинации
@dp.callback_query(F.data.startswith("page:"))
async def process_pagination(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action = parts[1]          # "set_base" или "select_target" и т.д.
    page = int(parts[2])
    currency_type = parts[3] if len(parts) > 3 else "all"

    # Определяем текущий текст в зависимости от действия
    if action == "set_base":
        text = "Выберите основную валюту из списка:"
    elif "select_base" in action:
        text = "Выберите исходную валюту:"
    elif "select_target" in action:
        text = "Выберите целевую валюту:"
    else:
        text = "Выберите валюту:"

    await callback.message.edit_caption(
        text,
        reply_markup=get_currency_keyboard(
            selected_currency=None,
            action=action,
            page=page,
            currency_type=currency_type
        )
    )
    await callback.answer()


# Новый хендлер для смены типа валют
@dp.callback_query(F.data.startswith("switch_type:"))
async def process_switch_type(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0
    currency_type = parts[3] if len(parts) > 3 else "all"

    # Текст в зависимости от действия
    if action == "set_base":
        text = "Выберите основную валюту из списка:"
    elif "select_base" in action:
        text = "Выберите исходную валюту:"
    elif "select_target" in action:
        text = "Выберите целевую валюту:"
    else:
        text = "Выберите валюту:"

    await callback.message.edit_caption(
        text,
        reply_markup=get_currency_keyboard(
            selected_currency=None,
            action=action,
            page=page,
            currency_type=currency_type
        )
    )
    await callback.answer()


# Новый хендлер для кнопки "Криптовалюты"
@dp.message(F.text == "₿ Криптовалюты")
async def show_crypto_menu(message: types.Message):
    user_id = message.from_user.id

    # Удаляем предыдущие сообщения
    await delete_previous_messages(user_id, keep_last=0)

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    await send_photo(
        message,
        "crypto_market",
        "₿ *Криптовалютный рынок*\n\nВыберите действие:",
        get_crypto_menu_keyboard(),
        "Markdown"
    )


@dp.callback_query(F.data.startswith("crypto_pair:"))
async def process_crypto_pair(callback: types.CallbackQuery):
    try:
        # Исправляем парсинг callback_data
        parts = callback.data.split(":")
        if len(parts) >= 3:
            base = parts[1]
            target = parts[2]
        else:
            await callback.answer("❌ Ошибка формата данных")
            return

        # Сначала отправляем текстовое сообщение о загрузке
        loading_msg = await callback.message.answer(f"🔄 Получаю курс {base}/{target}...")

        rate = await converter.get_exchange_rate(base, target)

        if rate:
            base_name = CRYPTOCURRENCIES.get(base, base)
            target_name = CURRENCIES.get(target, target)

            response_text = (
                    f"📊 *Курс криптовалюты*\n\n"
                    f"{base_name} → {target_name}\n\n"
                    f"💰 1 {base} = *${rate:,.2f}*\n"
                    f"🔄 1 USD = {1 / rate:.8f} {base}\n\n"
                    f"📅 *Обновлено:* " + datetime.now().strftime('%d.%m.%Y %H:%M')
            )

            # Редактируем текстовое сообщение
            await loading_msg.edit_text(response_text, parse_mode="Markdown")

            # Удаляем исходное сообщение (если оно было с фото)
            try:
                await callback.message.delete()
            except:
                pass

        else:
            await loading_msg.edit_text("❌ Не удалось получить курс. API может быть недоступен.")

    except Exception as e:
        print(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка")

    await callback.answer()


@dp.callback_query(F.data == "crypto_top")
async def show_top_crypto(callback: types.CallbackQuery):
    loading_msg = await safe_edit_caption(callback, "🔄 Загружаю реальные данные с бирж...")

    try:
        top_crypto = await converter.get_top_cryptocurrencies(10)

        if top_crypto:
            message_text = "🏆 *Топ-10 криптовалют (по рыночной капитализации)*\n\n"

            for i, crypto in enumerate(top_crypto, 1):
                symbol = crypto.get('symbol', '')
                name = crypto.get('name', '')
                price = crypto.get('price', 0)
                change = crypto.get('change', 0)

                # Определяем эмодзи для изменения цены
                change_emoji = "📈" if change >= 0 else "📉"
                change_color = "🟢" if change >= 0 else "🔴"

                # Форматируем цену в зависимости от величины
                if price < 0.0001:
                    price_str = f"${price:.8f}"
                elif price < 0.01:
                    price_str = f"${price:.6f}"
                elif price < 1:
                    price_str = f"${price:.4f}"
                elif price < 100:
                    price_str = f"${price:.2f}"
                elif price < 10000:
                    price_str = f"${price:,.2f}"
                else:
                    price_str = f"${price:,.0f}"

                message_text += (
                    f"{i}. *{name} ({symbol})*\n"
                    f"   💰 Цена: {price_str}\n"
                    f"   {change_emoji} Изменение за 24ч: {change_color} {change:+.2f}%\n\n"
                )

            message_text += "📊 *Источник:* CoinGecko API\n"
            message_text += "🔄 *Обновлено:* " + datetime.now().strftime('%d.%m.%Y %H:%M')

            await callback.message.delete()

            sent = await send_photo(
                callback.message,
                "top_crypto",
                message_text,
                reply_markup=get_top_crypto_keyboard(),
                parse_mode="Markdown"
            )

            if not sent:
                await callback.message.answer(
                    message_text,
                    parse_mode="Markdown",
                    reply_markup=get_top_crypto_keyboard()
                )
        else:
            await loading_msg.edit_text("❌ Не удалось загрузить данные с бирж")

    except Exception as e:
        print(f"Ошибка получения топа крипты: {e}")
        await loading_msg.edit_text(f"❌ Ошибка загрузки: {str(e)}")

    await callback.answer()


# Хендлер для детальной информации о криптовалюте
@dp.callback_query(F.data.startswith("crypto_detail:"))
async def show_crypto_detail(callback: types.CallbackQuery):
    crypto_code = callback.data.split(":")[1]

    loading_msg = await callback.message.edit_caption(f"🔄 Загружаю данные {crypto_code}...")

    try:
        # Получаем курсы для криптовалюты
        rates = await converter.get_all_rates(crypto_code)

        if rates:
            crypto_name = CRYPTOCURRENCIES.get(crypto_code, crypto_code)

            message_text = f"📊 *{crypto_name}*\n\n"
            message_text += f"*Курсы:*\n"

            # Показываем основные валюты
            main_currencies = ['USD', 'EUR', 'RUB', 'GBP', 'JPY']
            for currency in main_currencies:
                if currency in rates:
                    rate = rates[currency]
                    emoji = CURRENCIES.get(currency, '').split()[0] if currency in CURRENCIES else '💰'
                    message_text += f"{emoji} 1 {crypto_code} = {rate:.2f} {currency}\n"

            message_text += f"\n🔄 *Обновлено:* " + datetime.now().strftime('%d.%m.%Y %H:%M')

            await loading_msg.edit_caption(
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=get_top_crypto_keyboard()  # чтобы кнопки остались
            )
        else:
            await loading_msg.edit_text(f"❌ Не удалось получить данные для {crypto_code}")

    except Exception as e:
        await loading_msg.edit_caption(
            caption=f"Ошибка: {str(e)}",
            reply_markup=get_top_crypto_keyboard()
        )

    await callback.answer()


# Хендлер для кнопки "Новости"
@dp.message(F.text == "📰 Новости")
async def show_news_menu(message: types.Message):
    user_id = message.from_user.id

    # Удаляем предыдущие сообщения
    await delete_previous_messages(user_id, keep_last=0)

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    await send_photo(
        message,
        "news_menu",
        "📰 *Финансовые новости*\n\nВыберите категорию новостей:",
        get_news_menu_keyboard(),
        "Markdown"
    )


# Хендлер для последних новостей
@dp.callback_query(F.data == "news_latest")
async def show_latest_news(callback: types.CallbackQuery):
    try:
        news = await news_service.get_latest_financial_news(10)
        msg = news_service.format_news_message(news, "Последние финансовые новости")

        sent = await send_photo(
            callback.message,
            "latest_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка загрузки новостей: {str(e)}")

    await callback.answer()


@dp.callback_query(F.data == "news_finance")
async def show_us_news(callback: types.CallbackQuery):
    try:
        news = await news_service.get_us_financial_news(10)
        msg = news_service.format_news_message(news, "Финансовые новости")

        sent = await send_photo(
            callback.message,
            "financial_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


@dp.callback_query(F.data == "news_crypto")
async def show_crypto_news(callback: types.CallbackQuery):
    try:
        news = await news_service.get_crypto_news(10)
        msg = news_service.format_news_message(news, "Криптовалютные новости")

        sent = await send_photo(
            callback.message,
            "crypto_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


@dp.callback_query(F.data == "news_finance")
async def show_finance_news(callback: types.CallbackQuery):
    loading = await safe_edit_caption(callback, "Загружаю финансовые новости...")
    news = await news_service.get_financial_news("финансы OR инвестиции OR рынок", 10)
    msg = news_service.format_news_message(news, "Финансовые новости")

    await callback.message.delete()

    sent = await send_photo(
        callback.message,
        "financial_news",
        msg,
        parse_mode="Markdown"
    )

    if not sent:
        await callback.message.answer(
            msg,
            parse_mode="Markdown"
        )
    await callback.answer()


# Аналогично для других категорий новостей


# Хендлер для экономических новостей
@dp.callback_query(F.data == "news_economy")
async def show_economy_news(callback: types.CallbackQuery):
    try:
        news = await news_service.get_economic_news(10)
        msg = news_service.format_news_message(news, "Экономические новости")

        sent = await send_photo(
            callback.message,
            "economy_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


# Хендлер для новостей о банках
@dp.callback_query(F.data == "news_banking")
async def show_banking_news(callback: types.CallbackQuery):
    try:
        news = await news_service.get_banking_news(10)
        msg = news_service.format_news_message(news, "Новости банковского сектора")

        sent = await send_photo(
            callback.message,
            "banking_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


# Российские новости
@dp.callback_query(F.data == "news_russia")
async def show_russian_top(callback: types.CallbackQuery):
    try:
        news = await news_service.get_russian_top_news(10)
        msg = news_service.format_news_message(news, "РФ Все новости")

        sent = await send_photo(
            callback.message,
            "russia_news",
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


@dp.callback_query(F.data == "news_russia_finance")
async def show_russian_finance(callback: types.CallbackQuery):
    try:
        news = await news_service.get_russian_financial_news(10)
        msg = news_service.format_news_message(news, "РФ Финансы · Рынок")

        sent = await send_photo(
            callback.message,
            "financial_news",  # Используем ту же фотографию, что и для финансовых новостей
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        if not sent:
            await callback.message.answer(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


# Хендлер для возврата в криптоменю
@dp.callback_query(F.data == "crypto_back")
async def back_to_crypto_menu(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="Криптовалютный рынок\n\nВыберите действие:",
        reply_markup=get_crypto_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# Обновляем команду /convert для поддержки крипты
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message):
    args = message.text.split()

    if len(args) == 1:
        # Показываем быстрые пары, включая крипту
        await message.answer(
            "⚡ *Быстрая конвертация*\n\n"
            "Выберите валютную пару или используйте:\n"
            "`/convert <сумма> <из> <в>`\n\n"
            "Примеры:\n"
            "`/convert 100 USD EUR`\n"
            "`/convert 0.1 BTC USD`\n"
            "`/convert 5000 RUB BTC`",
            parse_mode="Markdown",
            reply_markup=get_quick_conversion_keyboard()
        )
    elif len(args) == 4:
        try:
            amount = float(args[1].replace(',', '.'))
            base_currency = args[2].upper()
            target_currency = args[3].upper()

            # Проверяем валюты
            if base_currency not in ALL_CURRENCIES:
                await message.answer(f"❌ Неизвестная валюта: {base_currency}")
                return
            if target_currency not in ALL_CURRENCIES:
                await message.answer(f"❌ Неизвестная валюта: {target_currency}")
                return

            # Конвертируем
            result = await converter.convert(amount, base_currency, target_currency)
            if result:
                rate = await converter.get_exchange_rate(base_currency, target_currency)

                # Получаем названия
                base_name = ALL_CURRENCIES.get(base_currency, base_currency)
                target_name = ALL_CURRENCIES.get(target_currency, target_currency)

                # Форматируем результат в зависимости от величины
                if result < 0.01:
                    result_str = f"{result:.8f}"
                elif result < 1:
                    result_str = f"{result:.6f}"
                elif result < 1000:
                    result_str = f"{result:.2f}"
                else:
                    result_str = f"{result:,.2f}".replace(',', ' ')

                response_text = (
                    f"💱 *Результат конвертации:*\n\n"
                    f"📥 {base_name}\n"
                    f"📤 {target_name}\n\n"
                    f"💰 {amount} {base_currency} = *{result_str} {target_currency}*\n\n"
                    f"📊 Курс: 1 {base_currency} = {rate:.8f} {target_currency}\n"
                    f"🔄 Обратный: 1 {target_currency} = {1 / rate:.8f} {base_currency}"
                )

                await message.answer(response_text, parse_mode="Markdown")
            else:
                await message.answer("❌ Ошибка при конвертации")

        except ValueError:
            await message.answer("❌ Неверный формат суммы. Используйте числа.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    else:
        await message.answer(
            "❌ *Неверный формат*\n\n"
            "✅ Используйте: `/convert <сумма> <из> <в>`\n\n"
            "📝 Примеры:\n"
            "`/convert 100 USD EUR`\n"
            "`/convert 0.05 BTC EUR`\n"
            "`/convert 10000 RUB BTC`\n\n"
            "🌍 Для списка всех валют нажмите '🌍 Все валюты'",
            parse_mode="Markdown"
        )


# Обновляем хендлер ввода суммы для работы с криптой
@dp.message(ConverterStates.enter_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть положительным числом!")
            return

        data = await state.get_data()
        base_currency = data.get('base_currency')
        target_currency = data.get('target_currency')

        # Получаем курс и конвертируем
        result = await converter.convert(amount, base_currency, target_currency)

        if result:
            # Форматируем вывод
            if result < 0.000001:
                result_str = f"{result:.10f}"
            elif result < 0.001:
                result_str = f"{result:.8f}"
            elif result < 0.01:
                result_str = f"{result:.6f}"
            elif result < 1:
                result_str = f"{result:.4f}"
            elif result < 1000:
                result_str = f"{result:.2f}"
            else:
                result_str = f"{result:,.2f}".replace(',', ' ')

            # Получаем текущий курс
            rate = await converter.get_exchange_rate(base_currency, target_currency)

            # Получаем названия валют
            base_name = ALL_CURRENCIES.get(base_currency, base_currency)
            target_name = ALL_CURRENCIES.get(target_currency, target_currency)

            response_text = (
                f"📊 *Результат конвертации:*\n\n"
                f"📥 {base_name}\n"
                f"📤 {target_name}\n\n"
                f"💰 {amount} {base_currency} = *{result_str} {target_currency}*\n\n"
                f"📈 Курс: 1 {base_currency} = {rate:.8f} {target_currency}\n"
                f"🔄 Обратный: 1 {target_currency} = {1 / rate:.8f} {base_currency}"
            )

            # Сохраняем в историю
            user_id = message.from_user.id
            if user_id not in user_data:
                user_data[user_id] = {
                    'base_currency': 'USD',
                    'conversion_history': []
                }

            if 'conversion_history' not in user_data[user_id]:
                user_data[user_id]['conversion_history'] = []

            history_entry = {
                'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'from': f"{amount} {base_currency}",
                'to': f"{result_str} {target_currency}",
                'rate': rate
            }
            user_data[user_id]['conversion_history'].append(history_entry)

            # Отправляем фотографию с результатом
            sent = await send_photo(
                message,
                "conversion_result",
                response_text,
                get_back_to_menu_keyboard(),
                "Markdown"
            )

            if not sent:
                await message.answer(response_text, parse_mode="Markdown", reply_markup=get_back_to_menu_keyboard())

            await state.clear()
        else:
            await message.answer("❌ Ошибка при получении курса. Попробуйте позже.")

    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")


# Кнопка "Все валюты"
@dp.message(F.text == "🌍 Все валюты")
async def show_all_currencies(message: types.Message):
    currencies_text = "🌍 *Все доступные валюты:*\n\n"

    # Группируем по алфавиту
    sorted_currencies = sorted(ALL_CURRENCIES.items())

    for code, name in sorted_currencies:
        currencies_text += f"{name}\n"

    currencies_text += f"\nВсего: {len(ALL_CURRENCIES)} валют"

    await message.answer(currencies_text, parse_mode="Markdown")


# Кнопка "Топ курсов"
@dp.message(F.text == "📈 Топ курсов")
async def show_top_rates(message: types.Message):
    user_id = message.from_user.id
    base_currency = user_data.get(user_id, {}).get('base_currency', 'USD')

    loading_msg = await message.answer("📊 Загружаю топ курсов...")

    try:
        rates = await converter.get_all_rates(base_currency)
        if not rates:
            await loading_msg.edit_text("❌ Ошибка загрузки")
            return

        # Убираем базовую валюту из списка
        rates_without_base = {code: rate for code, rate in rates.items() if
                              code != base_currency and code in ALL_CURRENCIES}

        # Получаем топ-5 самых дорогих валют относительно базовой
        sorted_rates_desc = sorted(rates_without_base.items(), key=lambda x: x[1], reverse=True)

        top_text = f"🏆 *Топ-5 самых дорогих валют относительно {base_currency}:*\n\n"

        for i, (code, rate) in enumerate(sorted_rates_desc[:5], 1):
            currency_name = ALL_CURRENCIES.get(code, code)
            top_text += f"{i}. {currency_name}\n"
            top_text += f"   1 {base_currency} = {rate:.4f} {code}\n\n"

        # Получаем топ-5 самых дешевых валют
        sorted_rates_asc = sorted(rates_without_base.items(), key=lambda x: x[1])

        top_text += f"📉 *Топ-5 самых дешевых валют относительно {base_currency}:*\n\n"

        for i, (code, rate) in enumerate(sorted_rates_asc[:5], 1):
            currency_name = ALL_CURRENCIES.get(code, code)
            top_text += f"{i}. {currency_name}\n"
            top_text += f"   1 {base_currency} = {rate:.6f} {code}\n\n"

        # Добавляем дополнительную информацию
        if sorted_rates_desc and sorted_rates_asc:
            most_expensive = sorted_rates_desc[0]
            cheapest = sorted_rates_asc[0]

            top_text += f"💡 *Интересные факты:*\n"
            top_text += f"• Самый высокий курс: 1 {base_currency} = {most_expensive[1]:.2f} {most_expensive[0]}\n"
            top_text += f"• Самый низкий курс: 1 {base_currency} = {cheapest[1]:.6f} {cheapest[0]}\n"
            top_text += f"• Разница: в {most_expensive[1] / cheapest[1]:.0f} раз"

        await loading_msg.edit_text(top_text, parse_mode="Markdown")

    except Exception as e:
        print(f"Ошибка в топ курсах: {e}")
        await loading_msg.edit_text("❌ Ошибка при загрузке топ курсов")


# Обработка установки базовой валюты
@dp.callback_query(F.data.startswith("set_base:"))
async def process_set_base(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Удаляем предыдущее сообщение с клавиатурой
    await delete_last_bot_message(user_id)

    # Сохраняем в данные пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    ensure_user_data(user_id)['base_currency'] = currency

    text = (
        f"✅ Основная валюта изменена на: {currency}\n\n"
        f"Теперь все курсы будут отображаться относительно {currency}"
    )

    await send_photo(
        callback.message,
        "base_currency_changed",
        text,
        get_back_to_menu_keyboard()
    )

    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "all_currencies")
async def show_all_currencies_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_caption(
        "Выберите основную валюту из списка:",
        reply_markup=get_currency_keyboard(None, "set_base")
    )
    await callback.answer()


# Обработка быстрой конвертации
@dp.callback_query(F.data.startswith("quick:"))
async def process_quick_conversion(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")

    # Должно быть ровно 3 части: quick, USD, EUR
    if len(parts) != 3:
        await callback.answer("Ошибка в данных. Попробуй ещё раз.")
        return

    _, base_currency, target_currency = parts

    await state.update_data({
        'base_currency': base_currency,
        'target_currency': target_currency
    })

    base_name = ALL_CURRENCIES.get(base_currency, base_currency)
    target_name = ALL_CURRENCIES.get(target_currency, target_currency)

    await callback.message.edit_text(
        f"⚡ *Быстрая конвертация:*\n"
        f"Из: {base_name}\n"
        f"В: {target_name}\n\n"
        f"Введите сумму для конвертации в {base_currency}:",
        parse_mode="Markdown"
    )
    await state.set_state(ConverterStates.enter_amount)
    await callback.answer()



# Обработка кнопки "Назад в меню"
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Было (падает):
    # base_currency = user_data[user_id]['base_currency']

    # Стало (никогда не упадёт):
    base_currency = ensure_user_data(user_id)['base_currency']

    welcome_text = (
        "💱 *Конвертер валют*\n\n"
        "Я помогу вам конвертировать валюты по актуальному курсу.\n\n"
        "Используйте кнопки ниже для работы с ботом:"
    )

    await send_photo(callback.message, "welcome", welcome_text, get_main_menu(), "Markdown")
    await callback.answer()


# Обработка отмены
@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Удаляем предыдущие сообщения
    await delete_previous_messages(user_id, keep_last=0)

    await send_photo(callback.message, "welcome", "❌ Операция отменена")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "news_search")
async def search_news(callback: types.CallbackQuery, state: FSMContext):
    # Отправляем новое сообщение вместо редактирования
    await callback.message.answer(
        "🔍 *Поиск новостей*\n\n"
        "Введите ключевое слово для поиска новостей:",
        parse_mode="Markdown"
    )
    await state.set_state(ConverterStates.enter_news_search)
    await callback.answer()



@dp.message(ConverterStates.enter_news_search)
async def process_news_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Пожалуйста, введите слово для поиска.")
        return

    loading_msg = await message.answer(f"Ищу новости по запросу «{query}»...")

    try:
        # ← ВОТ ТАК ДОЛЖНО БЫТЬ ТЕПЕРЬ:
        news = await news_service._fetch_newsapi(query=query, limit=10, language='en')

        # Если запрос на русском — ищем на русском
        if any(c in query.lower() for c in ['рубль', 'россия', 'москва', 'цб', 'санкции', 'нефть']):
            news = await news_service._fetch_newsapi(query=query, limit=10, language='ru')

        message_text = news_service.format_news_message(news, f"Результаты по запросу «{query}»")
        await loading_msg.edit_text(message_text, parse_mode="Markdown", disable_web_page_preview=True)
        await state.clear()

    except Exception as e:
        await loading_msg.edit_text(f"Ошибка поиска: {str(e)}")
        print(f"Ошибка поиска новостей: {e}")



@dp.callback_query(F.data == "crypto_top_refresh")
async def refresh_crypto_top(callback: types.CallbackQuery):
    await show_top_crypto(callback)
    await callback.answer()



@dp.callback_query(F.data == "convert_crypto")
async def convert_crypto_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_caption(
        "Выберите тип валют для конвертации:",
        reply_markup=get_currency_type_keyboard()
    )
    await state.set_state(ConverterStates.select_currency_type)
    await callback.answer()


@dp.callback_query(F.data == "crypto_chart")
async def show_crypto_chart(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        "📈 *Графики криптовалют*\n\n"
        "Эта функция в разработке. Скоро здесь появятся графики цен криптовалют!\n\n"
        "А пока вы можете посмотреть:\n"
        "• Топ криптовалют 📊\n"
        "• Курсы криптовалют 💱\n"
        "• Конвертацию крипты 🔄",
        parse_mode="Markdown"
    )
    await callback.answer()



@dp.callback_query(F.data == "news_finance")
async def show_finance_news(callback: types.CallbackQuery):
    loading_msg = await safe_edit_caption(callback,"🔄 Загружаю финансовые новости...")

    try:
        news = await news_service.get_financial_news("финансы OR инвестиции OR рынок", 10)
        message = news_service.format_news_message(news, "🇺🇸 Финансовые новости")

        await loading_msg.edit_text(
            message,
            parse_mode="Markdown"
        )

    except Exception as e:
        await loading_msg.edit_text(f"❌ Ошибка загрузки новостей: {str(e)}")

    await callback.answer()




async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())