import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import redis
import json

class BoraInvestir:

    def get_urls(self):
        list_url = []
        list_time = []
        list_title = []
        list_author = []
        list_subtitle = []
        list_font = []
        yesterday = date.today() - timedelta(days=1)
        yesterday = date.strftime(yesterday, "%Y-%m-%d")
        for i in range(1, 5):
            response = requests.get(f'https://borainvestir.b3.com.br/noticias/page/{i}')
            response.raise_for_status()
            print(f'Entrando Pagina {i}')
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('section', class_='feed-vertical')
            url = title.find_all('a', class_='feed-vertical__item')
            time = title.find_all('time')
            url = [x.get('href') for x in url]
            time = [x.get('datetime') for x in time]
            time = [x for x in time if x[:10] == yesterday]
            url = url[:len(time)]
            for x in url:
                content = self.get_content(x)
                list_title.append(content['title'])
                list_author.append(content['author'])
                list_subtitle.append(content['subtitle'])
                list_font.append("BoraInvestir")
            list_url = list_url + url
            list_time = list_time + time

        return {'data' : list_time, 'titulo' : list_title, 'url' : list_url, 'autor' : list_author, 'subtitulo' : list_subtitle, 'fonte' : list_font}

        

    def get_content(self, url):
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
        return {'title' : title, 'author' : author, 'subtitle' : subtitle}
    
    def run(self):
        data = self.get_urls()
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.publish('canal_scraping', json.dumps(data))