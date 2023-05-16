

import requests
from bs4 import BeautifulSoup
from app.Utils.RedisConnection import redisConnection
from datetime import datetime, timedelta
import json
from app.Utils.channelParameters import channel
redis = redisConnection()

class GoogleNews:
    def get_urls(self, message):
        # Envia uma solicitação para a URL e verifica a resposta
        print("reading googleNews")
        pt_url = 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYQjBMVUpTR2dKQ1VpZ0FQAQ?hl=pt-BR&gl' \
            '=BR&ceid=BR%3Apt-419 '
        eng_url = 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US' \
            '&ceid=US%3Aen '
        urls = [pt_url, eng_url]
        inicio = (datetime.today() - timedelta(days=365)).strftime("%d/%m/%Y")
        fim = (datetime.today()).strftime("%d/%m/%Y")
        urlDb = redis.get_newsletter({'inicio' : inicio, 'fim' : fim})
        urlDb = [x['url'] for x in urlDb]
        for url_language in urls:
            response = requests.get(url_language)
            response.raise_for_status()

            # Analisa o conteúdo HTML da página
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', {'class': 'UwIKyb'})
            for article in articles:
                try:
                    url = article.find('a', {'class': 'WwrzSb'})['href']
                    url = f"https://news.google.com{url[1:]}"
                    if(url in urlDb):
                        continue
                    text = article.find('h4', {'class': 'gPFEn'}).text
                    font_icon = article.find('img', {'class': 'qEdqNd'})['src']
                    font = article.find('span', {'class': 'vr1PYe'}).text
                    text = article.find('h4', {'class': 'gPFEn'}).text
                    date = article.find('time', {'class': 'hvbAAd'})['datetime']
                    date = datetime.strptime(date[:10], "%Y-%m-%d")
                    date = date.strftime("%d/%m/%Y")
                    content = {
                        'title': text,
                        'url': url,
                        'date': date,
                        'font': font,
                        'image': font_icon,
                        'language': "ptbr" if url_language == pt_url else "eng"
                    }
                    content['classification'] = redis.get_feedClassifier(content['title'])
                    print(content)
                    redis.r.publish(channel['saveData'], json.dumps(content))
                except:
                    pass