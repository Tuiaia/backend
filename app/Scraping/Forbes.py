from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
import json
from app.Utils.RedisConnection import redisConnection
from app.Utils.channelParameters import channel

# Create a Redis connection
redis = redisConnection()

class Forbes:
    def get_urls(self, message):
        # Get the date range for retrieving news from Forbes
        print("reading forbes")
        inicio = (datetime.today() - timedelta(days=365)).strftime("%d/%m/%Y")
        fim = (datetime.today()).strftime("%d/%m/%Y")

        # Retrieve the URLs from the Redis database
        urlDb = redis.get_newsletter({'inicio': inicio, 'fim': fim})
        urlDb = [x['url'] for x in urlDb]

        # Get today's date and format it for constructing the URL
        today = date.today()
        todayUrl = date.strftime(today, "%Y/%m/%d")
        dateSave = datetime.strftime(today, "%d/%m/%Y")

        # Fetch the Forbes webpage for today and parse the HTML
        response = requests.get(f'https://forbes.com.br/{todayUrl}')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the section containing the news articles
        title = soup.find('div', class_='col-12 resultado-desk')
        url = title.find_all('a', class_='link-title-post-1')

        # Extract the URLs of the articles that are not in the Redis database
        url = [x.get('href') for x in url if x.get('href') not in urlDb]

        # Process each URL and retrieve the content
        for x in url:
            content = self.get_content(x, dateSave)
            content['classification'] = redis.get_feedClassifier(content['title'])
            content['language'] = "ptbr"

            # Publish the content to a Redis channel for saving data
            redis.r.publish(channel['saveData'], json.dumps(content))

    def get_content(self, url, data):
        # Fetch the news article and parse the HTML
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the title from the news article
        title = soup.find('h1', class_="post__title").text

        # Create a dictionary containing the title, URL, date, font, and image of the news article
        return {'title': title, 'url': url, 'date': data, "font": "Forbes", 'image': "https://forbes.com.br/favicon-32x32.png"}
