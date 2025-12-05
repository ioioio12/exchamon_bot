import requests
import aiohttp
import asyncio
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from datetime import datetime
from data import CURRENCIES

load_dotenv()


class CurrencyConverter:
    def __init__(self):
        self.api_key = os.getenv('EXCHANGE_RATE_API_KEY')
        self.cryptocompare_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        self.coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')

        # Проверяем ключи
        print(f"DEBUG: ExchangeRate API key: {'ЕСТЬ' if self.api_key else 'НЕТ'}")
        print(f"DEBUG: CryptoCompare key: {'ЕСТЬ' if self.cryptocompare_key else 'НЕТ'}")
        print(f"DEBUG: CoinMarketCap key: {'ЕСТЬ' if self.coinmarketcap_key else 'НЕТ'}")

        self.base_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/" if self.api_key else None

    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:
        """Получить курс обмена между двумя валютами"""
        try:
            # Для криптовалют используем CryptoCompare
            if self._is_crypto(base_currency) or self._is_crypto(target_currency):
                return await self._get_crypto_rate_cryptocompare(base_currency, target_currency)

            # Для фиатных валют используем ExchangeRate-API
            if not self.base_url:
                return None

            url = f"{self.base_url}pair/{base_currency}/{target_currency}"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('result') == 'success':
                return data.get('conversion_rate')
            else:
                print(f"Ошибка ExchangeRate API: {data.get('error-type', 'Неизвестная ошибка')}")
                return None

        except Exception as e:
            print(f"Ошибка при получении курса: {e}")
            return None

    async def _get_crypto_rate_cryptocompare(self, base: str, target: str) -> Optional[float]:
        """Получить курс криптовалюты через CryptoCompare"""
        try:
            url = "https://min-api.cryptocompare.com/data/price"
            params = {
                'fsym': base,
                'tsyms': target,
                'api_key': self.cryptocompare_key if self.cryptocompare_key else ''
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if target in data:
                            return data[target]
                    else:
                        print(f"Ошибка CryptoCompare: {response.status}")
            return None

        except Exception as e:
            print(f"Ошибка CryptoCompare: {e}")
            return None

    def _is_crypto(self, currency_code: str) -> bool:
        """Проверить, является ли валюта криптовалютой"""
        crypto_codes = ['BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'USDT',
                        'USDC', 'DOT', 'MATIC', 'SHIB', 'AVAX', 'LTC', 'LINK', 'UNI',
                        'ATOM', 'DAI', 'TRX', 'XLM', 'ALGO', 'VET', 'XTZ', 'FIL',
                        'EOS', 'AAVE', 'SAND', 'MANA', 'AXS']
        return currency_code.upper() in crypto_codes

    async def get_top_cryptocurrencies(self, limit: int = 10) -> list:
        """Только CoinGecko — стабильный и быстрый"""
        top = await self._get_top_crypto_coingecko(limit)
        if top:
            return top
        else:
            print("Fallback на мок-данные")
            return self._get_mock_crypto_data()

        # try:
        #     if self.coinmarketcap_key:
        #         return await self._get_top_crypto_coinmarketcap(limit)
        #     elif self.cryptocompare_key:
        #         return await self._get_top_crypto_cryptocompare(limit)
        #     else:
        #         return await self._get_top_crypto_coingecko(limit)
        # except:
        #     return self._get_mock_crypto_data()

    async def _get_top_crypto_coinmarketcap(self, limit: int) -> list:
        """Используем CoinMarketCap API"""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.coinmarketcap_key,
                'Accept': 'application/json'
            }
            params = {
                'start': '1',
                'limit': str(limit),
                'convert': 'USD'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        top_crypto = []

                        for coin in data.get('data', []):
                            quote = coin.get('quote', {}).get('USD', {})
                            top_crypto.append({
                                'symbol': coin.get('symbol', ''),
                                'name': coin.get('name', ''),
                                'price': quote.get('price', 0),
                                'change': quote.get('percent_change_24h', 0),
                                'market_cap': quote.get('market_cap', 0)
                            })

                        return top_crypto
            return []

        except Exception as e:
            print(f"Ошибка CoinMarketCap: {e}")
            return []

    async def _get_top_crypto_cryptocompare(self, limit: int) -> list:
        """Используем CryptoCompare API"""
        try:
            url = "https://min-api.cryptocompare.com/data/top/mktcapfull"
            params = {
                'limit': limit,
                'tsym': 'USD',
                'api_key': self.cryptocompare_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        top_crypto = []

                        for coin in data.get('Data', [])[:limit]:
                            coin_info = coin.get('CoinInfo', {})
                            raw = coin.get('RAW', {}).get('USD', {})
                            display = coin.get('DISPLAY', {}).get('USD', {})

                            top_crypto.append({
                                'symbol': coin_info.get('Name', ''),
                                'name': coin_info.get('FullName', ''),
                                'price': raw.get('PRICE', 0),
                                'change': raw.get('CHANGEPCT24HOUR', 0),
                                'market_cap': raw.get('MKTCAP', 0)
                            })

                        return top_crypto
            return []

        except Exception as e:
            print(f"Ошибка CryptoCompare: {e}")
            return []

    async def _get_top_crypto_coingecko(self, limit: int) -> list:
        """CoinGecko с полной защитой от False/null и правильными % за 24ч"""
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            # Проверяем и конвертируем '24h' в строку (никогда не False)
            percentage_param = '24h'
            if not isinstance(percentage_param, str):
                percentage_param = '24h'  # fallback на строку

            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': str(limit),  # int → str для безопасности
                'page': '1',
                'sparkline': 'false',  # bool → str
                'price_change_percentage': percentage_param  # всегда str
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        print(f"CoinGecko HTTP: {response.status} - {await response.text()}")
                        return []

                    data = await response.json()
                    if not isinstance(data, list) or not data:
                        print("CoinGecko: пустой ответ")
                        return []

                    top_crypto = []
                    for coin in data[:limit]:
                        # Безопасная обработка change (поле 'price_change_percentage_24h')
                        change_raw = coin.get('price_change_percentage_24h')
                        if change_raw is None or change_raw is False:
                            change_24h = 0.0
                        else:
                            try:
                                change_24h = float(change_raw)
                            except (ValueError, TypeError):
                                change_24h = 0.0

                        # Безопасная цена
                        price_raw = coin.get('current_price')
                        price = float(price_raw) if price_raw and price_raw != 0 else 0.0

                        top_crypto.append({
                            'symbol': str(coin.get('symbol', '')).upper(),
                            'name': str(coin.get('name', '')),
                            'price': price,
                            'change': round(change_24h, 2),
                            'market_cap': float(coin.get('market_cap', 0)) if coin.get('market_cap') else 0
                        })

                    print(f"✅ CoinGecko: успешно получено {len(top_crypto)} монет")  # debug
                    return top_crypto

        except Exception as e:
            print(f"Полная ошибка CoinGecko: {type(e).__name__}: {e}")
            return []

    def _get_mock_crypto_data(self) -> list:
        """Мок-данные только если все API упали"""
        return [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'price': 68000.00, 'change': 2.5},
            {'symbol': 'ETH', 'name': 'Ethereum', 'price': 3500.00, 'change': 1.8},
            {'symbol': 'BNB', 'name': 'BNB', 'price': 580.00, 'change': 0.5},
            {'symbol': 'XRP', 'name': 'Ripple', 'price': 0.62, 'change': -0.3},
            {'symbol': 'SOL', 'name': 'Solana', 'price': 185.00, 'change': 5.2},
            {'symbol': 'ADA', 'name': 'Cardano', 'price': 0.68, 'change': 1.2},
            {'symbol': 'DOGE', 'name': 'Dogecoin', 'price': 0.15, 'change': 3.1},
            {'symbol': 'DOT', 'name': 'Polkadot', 'price': 9.50, 'change': -1.2},
            {'symbol': 'MATIC', 'name': 'Polygon', 'price': 1.05, 'change': 2.3},
            {'symbol': 'SHIB', 'name': 'Shiba Inu', 'price': 0.000028, 'change': 15.7}
        ]

    async def get_all_rates(self, base_currency: str) -> Dict[str, float]:
        """
        Возвращает курсы от base_currency ко всем валютам
        Работает с фиатом И криптовалютами (BTC, ETH, SOL и т.д.)
        """
        base_currency = base_currency.upper()

        # Если это криптовалюта — делаем через USD как промежуточную
        if self._is_crypto(base_currency):
            try:
                # 1. Получаем курс 1 base_crypto → USD
                crypto_to_usd = await self._get_crypto_rate_cryptocompare(base_currency, "USD")
                if not crypto_to_usd or crypto_to_usd <= 0:
                    print(f"Не удалось получить курс {base_currency} → USD")
                    return {}

                # 2. Получаем все фиатные курсы ОТ USD
                usd_rates = await self.get_all_rates("USD")
                if not usd_rates:
                    return {}

                # 3. Пересчитываем: 1 base_crypto = crypto_to_usd * (1 USD → target)
                result = {}
                for currency, rate_usd_to_target in usd_rates.items():
                    if currency == base_currency:
                        result[currency] = 1.0
                    else:
                        # ПРАВИЛЬНАЯ формула
                        result[currency] = crypto_to_usd * rate_usd_to_target
                return result

            except Exception as e:
                print(f"Ошибка при пересчёте от {base_currency}: {e}")
                return {}

        # Если это фиат — используем стандартный API
        else:
            try:
                if not self.base_url:
                    return {}

                url = f"{self.base_url}latest/{base_currency}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=15) as response:
                        if response.status != 200:
                            return {}
                        data = await response.json()

                        if data.get('result') == 'success':
                            rates = data.get('conversion_rates', {})
                            rates[base_currency] = 1.0  # на всякий случай
                            return rates
                        else:
                            print(f"ExchangeRate API ошибка: {data.get('error-type')}")
                            return {}

            except Exception as e:
                print(f"Ошибка get_all_rates({base_currency}): {e}")
                return {}

    async def convert(self, amount: float, base_currency: str, target_currency: str) -> Optional[float]:
        """Конвертировать сумму из одной валюты в другую"""
        rate = await self.get_exchange_rate(base_currency, target_currency)
        if rate:
            return amount * rate
        return None