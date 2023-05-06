import requests
from bs4 import BeautifulSoup
from datetime import datetime
import redis
import json
r = redis.Redis(host='redis', port=6379, db=0)


class BoraInvestir:

    def get_urls(self, message):
        urlDb = self.verify_url()
        for i in range(1, 5):
            response = requests.get(f'https://borainvestir.b3.com.br/noticias/page/{i}')
            response.raise_for_status()
            print(f'Entrando Pagina {i}')
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('section', class_='feed-vertical')
            url = title.find_all('a', class_='feed-vertical__item')
            time = title.find_all('time')

            url = [x.get('href') for x in url if x.get('href') not in urlDb]
            time = [x.get('datetime')[:10] for x in time[:len(url)]]
            for x, data in zip(url, time):
                content = self.get_content(x, data)
                r.publish('canal_scraping', json.dumps(content))

        
    def verify_url(self):
        r.publish('canal_newsletter', "get_news")
        pubsub = r.pubsub()
        pubsub.subscribe('canal_newsletterData')
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
                    return [json.loads(x)['url'] for x in json.loads(message['data'])]
                except:
                    pass

    def get_content(self, url, data):
        print(f"Acessando o link")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_="page-content__title").text
        try:
            author = soup.find('p', class_='journalist__item__name').text
        except:
            author = ""
        try:
            subtitle = soup.find('h2', class_="page-content__subtitle").text
        except:
            subtitle = ""
        return {'title' : title, 'author' : author, 'subtitle' : subtitle, 'url' : url, 'data' : data, "fonte" : "B3"}
    
    def run(self):
        p = r.pubsub()
        p.subscribe(**{'canal_feed': self.get_urls})
        p.run_in_thread(sleep_time=0.001)