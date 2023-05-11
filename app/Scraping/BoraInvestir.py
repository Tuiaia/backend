import requests
from bs4 import BeautifulSoup
import json
from app.Utils.RedisConnection import redisConnection

redis = redisConnection()

class BoraInvestir:

    def get_urls(self, message):
        urlDb = redis.get_newsletter()
        response = requests.get(f'https://borainvestir.b3.com.br/noticias/')
        response.raise_for_status()
        print(f'Entrando Pagina')
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('section', class_='feed-vertical')
        url = title.find_all('a', class_='feed-vertical__item')
        time = title.find_all('time')
        url = [x.get('href') for x in url if x.get('href') not in urlDb]
        time = [x.get('datetime')[:10] for x in time[:len(url)]]
        for x, data in zip(url, time):
            content = self.get_content(x, data)
            content['classification'] = redis.get_classifier(content['title'])
            redis.r.publish('canal_scraping', json.dumps(content))


    def get_content(self, url, data):
        print(f"Acessando o link")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_="page-content__title").text
        return {'title' : title, 'url' : url, 'data' : data, "fonte" : "B3"}
    