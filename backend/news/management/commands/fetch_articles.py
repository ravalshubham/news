from bs4 import BeautifulSoup

def strip_html(html):
    return BeautifulSoup(html, "html.parser").get_text()
import requests
from django.core.management.base import BaseCommand
from news.models import Article
from datetime import datetime
import feedparser

NEWSAPI_KEY = '5b1988d4abdf4cca84c2cb0728b73845'
NEWSAPI_URL = f'https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWSAPI_KEY}'
RSS_URL = 'https://rss.app/rss-feed?topicId=world'


from bs4 import BeautifulSoup

def strip_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

class Command(BaseCommand):
    help = 'Fetch articles from NewsAPI and RSS and store in DB.'

    def handle(self, *args, **kwargs):
        self.fetch_newsapi()
        self.fetch_rss()
        self.fetch_custom_sources()
        self.stdout.write(self.style.SUCCESS('Articles fetched and stored.'))

    def fetch_custom_sources(self):
        import feedparser
        sources = [
            # 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
            # 'https://rss.app/rss-feed?topicId=it-industry',
            # 'https://rss.app/rss-feed?keyword=game&region=US&lang=en',
            # 'https://rss.app/rss-feed?topicId=world',
            # 'https://rss.app/rss-feed?topicId=business',    
            # 'https://rss.app/rss-feed?topicId=health',
            # 'https://rss.app/rss-feed?topicId=entertainment',
            # 'https://rss.app/rss-feed?topicId=politics',
            # 'https://rss.app/rss-feed?keyword=game&region=US&lang=en'
            'https://rss.app/feeds/tU7C85WpZM2ezUEj.xml'
            
        ]
        for url in sources:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                image_url = ''
                # Try to extract image from media_content or links
                if 'media_content' in entry and entry.media_content:
                    image_url = entry.media_content[0].get('url', '')
                elif 'links' in entry:
                    for link in entry.links:
                        if link.get('type', '').startswith('image'):
                            image_url = link.get('href', '')
                            break
                if not image_url:
                    continue
                content = strip_html(entry.get('summary', ''))
                if 'Page cannot be found' in content:
                    continue
                Article.objects.get_or_create(
                    title=entry.get('title', '')[:255],
                    
                    defaults={
                        'image_url': image_url,
                        'content': content,
                        'category': 'Custom',
                        'tags': '',
                        'source': url,
                        'published_date': self.parse_date(entry.get('published')),
                        'language': 'en',
                        'author': entry.get('author', '') if 'author' in entry else ''
                    }
                )

        # For travelpulse and buzzfeednews, just store homepage as source (no RSS)
        for url in ['https://www.travelpulse.com/', 'https://www.buzzfeednews.com/']:
            # You can use requests and BeautifulSoup for real scraping, but here just store homepage as a placeholder
            pass
    def fetch_newsapi(self):
        resp = requests.get(NEWSAPI_URL)
        if resp.status_code == 200:
            for item in resp.json().get('articles', []):
                # Skip if no image
                if not item.get('urlToImage'):
                    continue

                # Fix category
                category = item.get('source', {}).get('name', 'NewsAPI')
                if isinstance(category, list):
                    category = category[0] if category else 'NewsAPI'
                elif not isinstance(category, str):
                    category = str(category)

                Article.objects.get_or_create(
                    title=item.get('title', '')[:255],
                    defaults={
                        'image_url': item.get('urlToImage'),
                        'content': item.get('content') or '',
                        'category': category,
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
            # Skip if no image (RSS may have media content)
            media_content = entry.get('media_content', [])
            image_url = media_content[0]['url'] if media_content else None
            if not image_url:
                continue

            Article.objects.get_or_create(
                title=entry.get('title', '')[:255],
                defaults={
                    'image_url': image_url,
                    'content': entry.get('summary') or '',
                    'category': 'World',
                    'tags': '',
                    'source': 'RSS',
                    'published_date': self.parse_date(entry.get('published')),
                    'language': 'en',
                    'author': entry.get('author', '') if 'author' in entry else ''
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
