from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from data import CURRENCIES, CRYPTOCURRENCIES, ALL_CURRENCIES, POPULAR_CURRENCIES


# Основное меню
def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💱 Конвертировать валюту"),
        KeyboardButton(text="₿ Криптовалюты")
    )
    builder.row(
        KeyboardButton(text="📊 Курсы валют"),
        KeyboardButton(text="📰 Новости")
    )
    builder.row(
        KeyboardButton(text="⚙️ Выбрать основную валюту"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    return builder.as_markup(resize_keyboard=True)


# Клавиатура для выбора типа валюты (фиат/крипто/все)
def get_currency_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🇺🇸 Фиатные валюты",
            callback_data="currency_type:fiat"
        ),
        InlineKeyboardButton(
            text="₿ Криптовалюты",
            callback_data="currency_type:crypto"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🌍 Все валюты",
            callback_data="currency_type:all"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    return builder.as_markup()


def get_currency_keyboard(
        selected_currency: str = None,
        action: str = "select",
        page: int = 0,
        currency_type: str = "all"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Фильтруем валюты по типу
    if currency_type == "fiat":
        currencies_dict = CURRENCIES
    elif currency_type == "crypto":
        currencies_dict = CRYPTOCURRENCIES
    else:
        currencies_dict = ALL_CURRENCIES

    all_currencies = list(currencies_dict.items())
    items_per_page = 12
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(all_currencies))
    current_page_currencies = all_currencies[start_idx:end_idx]

    # Создаем кнопки
    for i in range(0, len(current_page_currencies), 3):
        row = []
        for code, name in current_page_currencies[i:i + 3]:
            # Для криптовалют берем первое слово как эмодзи
            if ' ' in name:
                parts = name.split(' ', 1)
                emoji = parts[0] if len(parts) > 0 else '💰'
                currency_name = parts[1] if len(parts) > 1 else code
            else:
                emoji = '💰'
                currency_name = name

            button_text = f"{emoji} {code}"
            if code == selected_currency:
                button_text += " ✅"

            row.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"{action}:{code}:{page}:{currency_type}"
            ))
        builder.row(*row)

    # Пагинация
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"page:{action}:{page - 1}:{currency_type}"
        ))

    if end_idx < len(all_currencies):
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"page:{action}:{page + 1}:{currency_type}"
        ))

    if navigation_buttons:
        builder.row(*navigation_buttons)

    # Кнопки смены типа валют
    type_buttons = []
    if currency_type != "fiat":
        type_buttons.append(InlineKeyboardButton(
            text="🇺🇸 Фиат",
            callback_data=f"switch_type:{action}:0:fiat"
        ))
    if currency_type != "crypto":
        type_buttons.append(InlineKeyboardButton(
            text="₿ Крипто",
            callback_data=f"switch_type:{action}:0:crypto"
        ))
    if currency_type != "all":
        type_buttons.append(InlineKeyboardButton(
            text="🌍 Все",
            callback_data=f"switch_type:{action}:0:all"
        ))

    if type_buttons:
        builder.row(*type_buttons)

    builder.row(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))

    return builder.as_markup()


# Клавиатура для криптовалютного меню
def get_crypto_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Топ криптовалют - исправляем формат callback_data
    crypto_pairs = [
        ("₿ BTC/USD", "crypto_pair:BTC:USD"),
        ("Ξ ETH/USD", "crypto_pair:ETH:USD"),
        ("⛓️ BNB/USD", "crypto_pair:BNB:USD"),
        ("✖️ XRP/USD", "crypto_pair:XRP:USD"),
        ("◎ SOL/USD", "crypto_pair:SOL:USD"),
        ("🅰️ ADA/USD", "crypto_pair:ADA:USD"),
        ("🐕 DOGE/USD", "crypto_pair:DOGE:USD"),
        ("💵 USDT/USD", "crypto_pair:USDT:USD"),
        ("● DOT/USD", "crypto_pair:DOT:USD"),
        ("⬢ MATIC/USD", "crypto_pair:MATIC:USD")
    ]

    for i in range(0, len(crypto_pairs), 2):
        row = []
        for text, callback_data in crypto_pairs[i:i + 2]:
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=callback_data  # Используем готовый callback_data
            ))
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(
            text="📊 Топ криптовалют",
            callback_data="crypto_top"
        ),
        InlineKeyboardButton(
            text="📈 График",
            callback_data="crypto_chart"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="💱 Конвертировать крипту",
            callback_data="convert_crypto"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()


# Клавиатура для новостей
def get_news_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📰 Последние новости",
            callback_data="news_latest"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="💰 Финансовые новости",
            callback_data="news_finance"
        ),
        InlineKeyboardButton(
            text="₿ Криптоновости",
            callback_data="news_crypto"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📈 Экономика",
            callback_data="news_economy"
        ),
        InlineKeyboardButton(
            text="🏦 Банки",
            callback_data="news_banking"
        )
    )

    # ← НОВЫЕ РОССИЙСКИЕ КНОПКИ
    builder.row(
        InlineKeyboardButton(
            text="🇷🇺 РФ Новости",
            callback_data="news_russia"
        ),
        InlineKeyboardButton(
            text="💎 РФ Финансы",
            callback_data="news_russia_finance"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🔍 Поиск новостей",
            callback_data="news_search"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()

# Клавиатура для топ криптовалют
def get_top_crypto_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Топ-10 криптовалют
    top_crypto = [
        ("₿ Bitcoin (BTC)", "BTC"),
        ("Ξ Ethereum (ETH)", "ETH"),
        ("⛓️ BNB (BNB)", "BNB"),
        ("✖️ Ripple (XRP)", "XRP"),
        ("◎ Solana (SOL)", "SOL"),
        ("🅰️ Cardano (ADA)", "ADA"),
        ("🐕 Dogecoin (DOGE)", "DOGE"),
        ("💵 Tether (USDT)", "USDT"),
        ("● Polkadot (DOT)", "DOT"),
        ("⬢ Polygon (MATIC)", "MATIC")
    ]

    for text, code in top_crypto:
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"crypto_detail:{code}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="crypto_top_refresh"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="crypto_back"
        )
    )

    return builder.as_markup()


# Клавиатура для выбора базовой валюты (топ популярных с флагами)
def get_base_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Группируем популярные валюты по 4 в ряд
    for i in range(0, len(POPULAR_CURRENCIES), 4):
        row = []
        for code in POPULAR_CURRENCIES[i:i + 4]:
            if code in CURRENCIES:
                name_parts = CURRENCIES[code].split(' ', 1)
                emoji = name_parts[0] if len(name_parts) > 0 else '💰'
                row.append(InlineKeyboardButton(
                    text=f"{emoji} {code}",
                    callback_data=f"set_base:{code}"
                ))
        builder.row(*row)

    builder.row(InlineKeyboardButton(
        text="🌍 Все валюты",
        callback_data="all_currencies"
    ))

    return builder.as_markup()


# Быстрая клавиатура для конвертации (популярные пары)
def get_quick_conversion_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Популярные валютные пары
    popular_pairs = [
        ("🇺🇸 USD → 🇪🇺 EUR", "USD:EUR"),
        ("🇪🇺 EUR → 🇺🇸 USD", "EUR:USD"),
        ("🇺🇸 USD → 🇷🇺 RUB", "USD:RUB"),
        ("🇷🇺 RUB → 🇺🇸 USD", "RUB:USD"),
        ("🇪🇺 EUR → 🇷🇺 RUB", "EUR:RUB"),
        ("🇷🇺 RUB → 🇪🇺 EUR", "RUB:EUR"),
        ("🇺🇸 USD → 🇰🇿 KZT", "USD:KZT"),
        ("🇰🇿 KZT → 🇺🇸 USD", "KZT:USD"),
        ("🇷🇺 RUB → 🇰🇿 KZT", "RUB:KZT"),
        ("🇰🇿 KZT → 🇷🇺 RUB", "KZT:RUB")
    ]

    for i in range(0, len(popular_pairs), 2):
        row = []
        for text, pair in popular_pairs[i:i + 2]:
            base, target = pair.split(':')
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=f"quick:{pair}"
            ))
        builder.row(*row)

    builder.row(InlineKeyboardButton(
        text="🔙 Назад в меню",
        callback_data="back_to_menu"
    ))

    return builder.as_markup()


# Клавиатура возврата в меню
def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔙 Назад в меню",
        callback_data="back_to_menu"
    ))
    return builder.as_markup()