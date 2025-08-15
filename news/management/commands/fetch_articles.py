import requests
from django.core.management.base import BaseCommand
from news.models import Article
from datetime import datetime
import feedparser

NEWSAPI_KEY = '5b1988d4abdf4cca84c2cb0728b73845'
NEWSAPI_URL = f'https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWSAPI_KEY}'
RSS_URL = 'https://rss.app/rss-feed?topicId=world'
NEWSDATA_URL = 'https://newsdata.io/api/1/latest?apikey=pub_dd43a7faa46146ccb08a698a485a1859&q=world'

class Command(BaseCommand):
    help = 'Fetch articles from NewsAPI, RSS, and NewsData.io and store in DB.'

    def handle(self, *args, **kwargs):
        self.fetch_newsapi()
        self.fetch_rss()
        self.fetch_newsdata()
        self.stdout.write(self.style.SUCCESS('Articles fetched and stored.'))

    def fetch_newsapi(self):
        resp = requests.get(NEWSAPI_URL)
        if resp.status_code == 200:
            for item in resp.json().get('articles', []):
                Article.objects.get_or_create(
                    title=item.get('title', '')[:255],
                    defaults={
                        'image_url': item.get('urlToImage'),
                        'content': item.get('content') or '',
                        'category': item.get('source', {}).get('name', 'NewsAPI'),
                        'tags': '',
                        'source': 'NewsAPI',
                        'published_date': self.parse_date(item.get('publishedAt')),
                        'language': 'en',
                        'author': item.get('author', '')
                    }
                )

    def fetch_rss(self):
        feed = feedparser.parse(RSS_URL)
        for entry in feed.entries:
            Article.objects.get_or_create(
                title=entry.get('title', '')[:255],
                defaults={
                    'image_url': '',
                    'content': entry.get('summary') or '',
                    'category': 'World',
                    'tags': '',
                    'source': 'RSS',
                    'published_date': self.parse_date(entry.get('published')), 
                    'language': 'en',
                    'author': entry.get('author', '') if 'author' in entry else ''
                }
            )

    def fetch_newsdata(self):
        resp = requests.get(NEWSDATA_URL)
        if resp.status_code == 200:
            for item in resp.json().get('results', []):
                Article.objects.get_or_create(
                    title=item.get('title', '')[:255],
                    defaults={
                        'image_url': item.get('image_url', ''),
                        'content': item.get('description') or '',
                        'category': item.get('category', 'World'),
                        'tags': ','.join(item.get('keywords', [])),
                        'source': 'NewsData.io',
                        'published_date': self.parse_date(item.get('pubDate')),
                        'language': item.get('language', 'en'),
                        'author': item.get('creator', '')
                    }
                )

    def parse_date(self, date_str):
        if not date_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            try:
                return datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
            except Exception:
                return datetime.now()
