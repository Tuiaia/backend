import requests
from bs4 import BeautifulSoup
import json
from app.Utils.RedisConnection import redisConnection
from datetime import datetime
from app.Utils.channelParameters import channel
from datetime import datetime, timedelta
from langdetect import detect
redis = redisConnection()

class BoraInvestir:

    def get_urls(self, message):
        inicio = (datetime.today() - timedelta(days=365)).strftime("%d/%m/%Y")
        fim = (datetime.today()).strftime("%d/%m/%Y")
        print("reading b3")
        urlDb = redis.get_newsletter({'inicio' : inicio, 'fim' : fim})
        urlDb = [x['url'] for x in urlDb]
        response = requests.get(f'https://borainvestir.b3.com.br/noticias/')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('section', class_='feed-vertical')
        url = title.find_all('a', class_='feed-vertical__item')
        time = title.find_all('time')
        url = [x.get('href') for x in url if x.get('href') not in urlDb]
        time = [x.get('datetime')[:10] for x in time[:len(url)]]
        time = [datetime.strptime(x, "%Y-%m-%d") for x in time]
        time = [datetime.strftime(x, "%d/%m/%Y") for x in time]
        for x, data in zip(url, time):
            content = self.get_content(x, data)
            content['classification'] = redis.get_feedClassifier(content['title'])
            content['language'] = "ptbr"
            redis.r.publish(channel['saveData'], json.dumps(content))


    def get_content(self, url, data):
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_="page-content__title").text
        return {'title' : title, 'url' : url, 'date' : data, "font" : "B3", "image" : "https://borainvestir.b3.com.br/app/themes/b3-br/assets/images/favicon/32.png"}
    