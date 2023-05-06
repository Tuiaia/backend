from datetime import date, datetime
from bs4 import BeautifulSoup
import requests
import redis
import json

r = redis.Redis(host='redis', port=6379)


class Forbes:
    def get_urls(self, message):
        urlDb = self.verify_url()
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
        title = soup.find('h1', class_="post__title").text
        try:
            teste = soup.find_all('header')[1]
            author = teste.find('span').text
        except:
            author = ""
        try:
            subtitle = soup.find('h2', class_="post__excerpt").text
        except:
            subtitle = ""
        return {'title' : title, 'author' : author, 'subtitle' : subtitle, 'url' : url, 'data' : data, "fonte" : "Forbes"}
    
    def run(self):
        p = r.pubsub()
        p.subscribe(**{'canal_feed': self.get_urls})
        p.run_in_thread(sleep_time=0.001)
