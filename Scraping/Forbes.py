from datetime import date, timedelta
from bs4 import BeautifulSoup
import requests
import redis
import json

class Forbes:
    def get_urls(self):
        r = redis.Redis(host='localhost', port=6379, db=0)
        yesterday = date.today() - timedelta(days=1)
        yesterday = date.strftime(yesterday, "%Y/%m/%d")
        response = requests.get(f'https://forbes.com.br/{yesterday}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', class_='col-12 resultado-desk')
        url = title.find_all('a', class_='link-title-post-1')
        url = [x.get('href') for x in url]
        for x in url:
            content = self.get_content(x, yesterday)
            r.publish('canal_scraping', json.dumps(content))

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
        return {'title' : title, 'author' : author, 'subtitle' : subtitle, 'url' : url, 'data' : data}
    
    def run(self):
        self.get_urls()
