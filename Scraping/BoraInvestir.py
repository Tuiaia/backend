import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, timedelta
from Data.DataStructure import ConjuntoDados

class BoraInvestir:
    def __init__(self) -> None:
        dados = ConjuntoDados()
    
    def get_total_pages():
        response = requests.get('https://borainvestir.b3.com.br/noticias/')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        pages = soup.find_all('a', class_='page-numbers')
        last_page = [x.text for x in pages][2]
        return int(last_page[8:])

    def get_urls(self):
        list_url = []
        list_time = []
        yesterday = date.today() - timedelta(days = 1)
        for i in range(1, self.get_total_pages()):
            response = requests.get(f'https://borainvestir.b3.com.br/noticias/page/{i}')
            response.raise_for_status()
            print(f'Entrando Pagina {i}')
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('section', class_='feed-vertical')
            url = title.find_all('a', class_='feed-vertical__item')
            time = title.find_all('time')
            list_url = list_url + [x.get('href') for x in url]
            list_time = list_time + [x.get('datetime') for x in time]

        self.dados.df['data'] = list_time
        self.dados.df['urls'] = list_url

    def get_content(self):
        list_title = list()
        list_author = list()
        list_text = list()
        for count, url in enumerate(self.dados.df['url']):
            print(f"Acessando o link {count}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('h1', class_="page-content__title").text
            try:
                author = soup.find('p', class_='journalist__item__name').text
            except:
                author = ""
            text = soup.find('div', class_="page-content__text").text
            list_author.append(author)
            list_text.append(text)
            list_title.append(title)
        self.dados.df['text'] = list_text
        self.dados.df['author'] = list_author
        self.dados.df['title'] = list_title
yesterday = date.today() - timedelta(days = 1)
print(yesterday)