from enum import Enum

# Расширенный список валют с флагами стран
CURRENCIES = {
    'USD': '🇺🇸 Доллар США',
    'EUR': '🇪🇺 Евро',
    'RUB': '🇷🇺 Российский рубль',
    'GBP': '🇬🇧 Фунт стерлингов',
    'JPY': '🇯🇵 Японская йена',
    'CNY': '🇨🇳 Китайский юань',
    'CHF': '🇨🇭 Швейцарский франк',
    'CAD': '🇨🇦 Канадский доллар',
    'AUD': '🇦🇺 Австралийский доллар',
    'NZD': '🇳🇿 Новозеландский доллар',
    'SGD': '🇸🇬 Сингапурский доллар',
    'HKD': '🇭🇰 Гонконгский доллар',
    'KRW': '🇰🇷 Южнокорейская вона',
    'INR': '🇮🇳 Индийская рупия',
    'BRL': '🇧🇷 Бразильский реал',
    'MXN': '🇲🇽 Мексиканское песо',
    'TRY': '🇹🇷 Турецкая лира',
    'ZAR': '🇿🇦 Южноафриканский рэнд',
    'SEK': '🇸🇪 Шведская крона',
    'NOK': '🇳🇴 Норвежская крона',
    'DKK': '🇩🇰 Датская крона',
    'PLN': '🇵🇱 Польский злотый',
    'CZK': '🇨🇿 Чешская крона',
    'HUF': '🇭🇺 Венгерский форинт',
    'RON': '🇷🇴 Румынский лей',
    'ILS': '🇮🇱 Израильский шекель',
    'AED': '🇦🇪 Дирхам ОАЭ',
    'SAR': '🇸🇦 Саудовский риял',
    'THB': '🇹🇭 Тайский бат',
    'MYR': '🇲🇾 Малайзийский ринггит',
    'IDR': '🇮🇩 Индонезийская рупия',
    'PHP': '🇵🇭 Филиппинское песо',
    'VND': '🇻🇳 Вьетнамский донг',
    'KZT': '🇰🇿 Казахстанский тенге',
    'UAH': '🇺🇦 Украинская гривна',
    'BYN': '🇧🇾 Белорусский рубль',
    'AMD': '🇦🇲 Армянский драм',
    'GEL': '🇬🇪 Грузинский лари',
    'AZN': '🇦🇿 Азербайджанский манат',
    'KGS': '🇰🇬 Киргизский сом',
    'UZS': '🇺🇿 Узбекский сум',
    'TJS': '🇹🇯 Таджикский сомони',
    'MDL': '🇲🇩 Молдавский лей',
    'BGN': '🇧🇬 Болгарский лев',
    'RSD': '🇷🇸 Сербский динар',
    'HRK': '🇭🇷 Хорватская куна',
    'ISK': '🇮🇸 Исландская крона',
    'EGP': '🇪🇬 Египетский фунт'
}

# Для удобства - топ популярных валют для быстрого выбора
POPULAR_CURRENCIES = [
    'USD', 'EUR', 'RUB', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD',
    'AUD', 'TRY', 'KZT', 'UAH', 'BYN', 'AED', 'INR', 'KRW', 'SGD'
]

class States(Enum):
    SELECT_BASE = "select_base"
    SELECT_TARGET = "select_target"
    ENTER_AMOUNT = "enter_amount"


CRYPTOCURRENCIES = {
    'BTC': '₿ Bitcoin',
    'ETH': 'Ξ Ethereum',
    'BNB': '⛓️ BNB',
    'XRP': '✖️ Ripple',
    'SOL': '◎ Solana',
    'ADA': '🅰️ Cardano',
    'DOGE': '🐕 Dogecoin',
    'DOT': '● Polkadot',
    'MATIC': '⬢ Polygon',
    'SHIB': '🐕 Shiba Inu',
    'AVAX': '❄️ Avalanche',
    'LTC': 'Ł Litecoin',
    'LINK': '🔗 Chainlink',
    'UNI': '🦄 Uniswap',
    'ATOM': '⚛️ Cosmos',
    'USDT': '💵 Tether',
    'USDC': '💵 USD Coin',
    'DAI': '💵 DAI',
    'TRX': '🚀 Tron',
    'XLM': '🌟 Stellar',
    'ALGO': '🔺 Algorand',
    'VET': '🔷 VeChain',
    'XTZ': '🍃 Tezos',
    'FIL': '📁 Filecoin',
    'EOS': 'ε EOS',
    'AAVE': '👻 Aave',
    'SAND': '🏖️ The Sandbox',
    'MANA': '🧙 Decentraland',
    'AXS': '🪙 Axie Infinity'
}

# Все валюты вместе (фиатные + крипто)
ALL_CURRENCIES = {**CURRENCIES, **CRYPTOCURRENCIES}

# Топ криптовалют для быстрого выбора
TOP_CRYPTO = ['BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'USDT', 'USDC', 'DOT']

# Категории валют для фильтрации
class CurrencyType(Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"
    ALL = "all"

# Для удобства - топ популярных валют для быстрого выбора
POPULAR_CURRENCIES = [
    'USD', 'EUR', 'RUB', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD',
    'AUD', 'TRY', 'KZT', 'UAH', 'BYN', 'AED', 'INR', 'KRW', 'SGD'
]

class States(Enum):
    SELECT_BASE = "select_base"
    SELECT_TARGET = "select_target"
    ENTER_AMOUNT = "enter_amount"
    SELECT_CURRENCY_TYPE = "select_currency_type"