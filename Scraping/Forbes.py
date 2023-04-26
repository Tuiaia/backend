from datetime import date, timedelta
from bs4 import BeautifulSoup
import requests

class Forbes:
    def get_urls(self):
        list_time = []
        list_title = []
        list_author = []
        list_subtitle = []
        list_font = []
        yesterday = date.today() - timedelta(days=1)
        yesterday = date.strftime(yesterday, "%Y/%m/%d")
        response = requests.get(f'https://forbes.com.br/{yesterday}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('div', class_='col-12 resultado-desk')
        url = title.find_all('a', class_='link-title-post-1')
        url = [x.get('href') for x in url]
        for x in url:
            content = self.get_content(x)
            list_title.append(content['title'])
            list_author.append(content['author'])
            list_subtitle.append(content['subtitle'])
            list_font.append("Forbes")
            list_time.append(yesterday)

        return [list_time, list_title, url, list_author, list_subtitle, list_font]

    def get_content(self, url):
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
        return {'title' : title, 'author' : author, 'subtitle' : subtitle}
    