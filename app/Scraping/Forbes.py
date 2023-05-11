from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
import json
from app.Utils.RedisConnection import redisConnection

redis = redisConnection()

class Forbes:
    def get_urls(self, message):
        urlDb = redis.get_newsletter()
        today = date.today()
        todayUrl = date.strftime(today, "%Y/%m/%d")
        dateSave = datetime.strftime(today, "%Y-%m-%d")
        response = requests.get(f'https://forbes.com.br/{todayUrl}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', class_='col-12 resultado-desk')
        url = title.find_all('a', class_='link-title-post-1')
        url = [x.get('href') for x in url if x.get('href') not in urlDb]
        for x in url:
            content = self.get_content(x, dateSave)
            content['classification'] = redis.get_classifier(content['title'])
            redis.r.publish('canal_scraping', json.dumps(content))

    def get_content(self, url, data):
        print(f"Acessando o link")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_="post__title").text
        return {'title' : title, 'url' : url, 'data' : data, "fonte" : "Forbes"}