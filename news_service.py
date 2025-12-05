# news_service.py
import aiohttp
import os
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class NewsService:
    def __init__(self):
        self.newsapi_key = os.getenv('NEWS_API_KEY')
        self.cryptopanic_key = os.getenv('CRYPTO_PANIC_KEY')

    async def _fetch_newsapi(self, query="", limit=10, country=None, language='en'):
        """Универсальная обёртка над NewsAPI — работает даже на бесплатном тарифе"""
        if not self.newsapi_key:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                if not query and country:
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {
                        'apiKey': self.newsapi_key,
                        'category': 'business',
                        'country': country,
                        'pageSize': limit,
                        'language': language
                    }
                else:
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        'apiKey': self.newsapi_key,
                        'q': query,
                        'language': language,
                        'sortBy': 'publishedAt',
                        'pageSize': limit
                    }

                async with session.get(url, params=params, timeout=15) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    articles = data.get('articles', [])
                    result = []
                    for a in articles[:limit]:
                        result.append({
                            'title': a.get('title', 'Без заголовка'),
                            'url': a.get('url', ''),
                            'source': a.get('source', {}).get('name', 'Unknown'),
                            'published_at': a.get('publishedAt', ''),
                        })
                    return result
        except Exception as e:
            print(f"NewsAPI ошибка: {e}")
            return []

    async def get_crypto_news(self, limit: int = 10):
        """Криптоновости с нормальными источниками"""
        if not self.cryptopanic_key:
            return await self._fetch_newsapi("bitcoin OR ethereum OR crypto OR blockchain", limit)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params={'auth_token': self.cryptopanic_key, 'public': 'true', 'filter': 'hot'},
                    timeout=20
                ) as resp:
                    if resp.status != 200:
                        return await self._fetch_newsapi("bitcoin OR ethereum OR crypto", limit)

                    data = await resp.json()
                    results = data.get('results', [])
                    out = []
                    for item in results[:limit]:
                        raw_url = item.get('url', '')
                        domain = urlparse(raw_url).netloc.replace('www.', '') if raw_url else 'CryptoPanic'
                        source = item.get('source', {}).get('title') or domain
                        out.append({
                            'title': item.get('title', ''),
                            'url': raw_url,
                            'source': source,
                            'published_at': item.get('published_at', ''),
                            'currencies': [c['code'] for c in item.get('currencies', [])][:3],
                        })
                    return out
        except Exception as e:
            print(f"CryptoPanic ошибка: {e}")
            return await self._fetch_newsapi("bitcoin OR ethereum OR crypto", limit)

    async def get_latest_financial_news(self, limit: int = 10):
        q = 'business OR finance OR stock OR market OR economy OR "wall street" OR fed OR "interest rates"'
        return await self._fetch_newsapi(q, limit)

    async def get_us_financial_news(self, limit: int = 10):
        q = '(business OR finance OR economy OR market OR fed OR "interest rates") AND (us OR "united states" OR usa)'
        return await self._fetch_newsapi(q, limit)

    async def get_economic_news(self, limit: int = 10):
        q = 'economy OR GDP OR inflation OR "interest rates" OR unemployment -sports -football'
        return await self._fetch_newsapi(q, limit)

    async def get_banking_news(self, limit: int = 10):
        q = '"central bank" OR "federal reserve" OR ECB OR "monetary policy" OR banks -sports -river'
        return await self._fetch_newsapi(q, limit)

    async def get_russian_top_news(self, limit: int = 10):
        """РФ Все новости — всегда с новостями, даже если top-headlines пустой"""
        # 1. Пробуем top-headlines (самые горячие)
        news = await self._fetch_newsapi(country='ru', limit=limit, language='ru')
        if news and len(news) >= 2:
            return news

        # 2. Если топ пустой — берём просто самые свежие русскоязычные новости за последние 48 часов
        news = await self._fetch_newsapi(
            query="",
            limit=limit,
            language='ru'
        )
        if news:
            return news

        # 3. Крайний fallback — ищем по общим словам, которые всегда есть
        return await self._fetch_newsapi(
            query="россия OR москва OR путин OR россияне OR рубль OR новости",
            limit=limit,
            language='ru'
        )

    async def get_russian_financial_news(self, limit: int = 10):
        """Финансовые и рыночные новости РФ — 100% всегда есть"""
        # Убрали lang:ru — он не работает в бесплатной версии
        query = '(' \
                'финансы OR экономика OR рубль OR доллар OR евро OR "курс рубля" OR биржа OR Мосбиржа ' \
                'OR "центральный банк" OR ЦБ OR "ключевая ставка" OR нефть OR газпром OR санкции ' \
                'OR инфляция OR ВВП OR бюджет OR "ставка ЦБ" OR "курс доллара" OR "курс евро"' \
                ')'
        return await self._fetch_newsapi(query=query, limit=limit, language='ru')

    def format_news_message(self, news_items, title: str = "Новости"):
        if not news_items:
            return f"*{title}*\n\nНовости не найдены"

        message = f"*{title}*\n\n"
        for i, item in enumerate(news_items[:5], 1):
            title_text = item.get('title', 'Без заголовка')
            source = item.get('source', 'Неизвестно')
            url = item.get('url', '#')
            if len(title_text) > 100:
                title_text = title_text[:97] + "..."

            message += f"{i}. [{title_text}]({url})\n"
            message += f"   Источник: *{source}*\n"
            if item.get('currencies'):
                message += f"   Валюты: {', '.join(item['currencies'])}\n"
            if item.get('published_at'):
                pub_date = item['published_at'][:10].replace('-', '.')
                message += f"   Дата: {pub_date}\n"
            message += "\n"

        message += f"Всего новостей: {len(news_items)}\n"
        message += f"Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        message += "\n*Нажмите на заголовок для перехода к источнику*"
        return message