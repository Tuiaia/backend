import pandas as pd
import re
import snscrape.modules.twitter as sns
import snscrape.modules.twitter as sntwitter
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup
import schedule
import time

def get_tweets(max_tweets = 500):
    max_results = max_tweets
    i = 0
    df_tweets = []
    current_date = date.today()
    current_end_date = current_date
    fim = current_date.strftime("%Y-%m-%d")
    inicio = current_end_date.strftime("%Y-%m-%d")
    print(inicio, fim)
    for tweet in sntwitter.TwitterSearchScraper(f'infomoney since:2023-04-19').get_items():
        if i > max_results:
            break
        df_tweets.append([tweet.date, tweet.rawContent])
        i = i + 1
    return pd.DataFrame(df_tweets, columns = ['data', 'titulo'])

def get_url_from_text(datafilm):
    urls = list()
    for count, text in enumerate(datafilm['titulo']):
        url = re.findall('https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)[0]
        urls.append(url)
        datafilm.loc[count, 'titulo'] = text.replace(url, '')
    datafilm['urls'] = urls
    return datafilm

def format_text(text):
    # Remove espaços e quebras de linha excessivos
    text = re.sub(r'\s+', ' ', text).strip()

    # Adiciona um espaço após a pontuação, se necessário
    text = re.sub(r'([.,;?!])([^\s])', r'\1 \2', text)
    text = text.replace('CONTINUA DEPOIS DA PUBLICIDADE', '').replace('Relacionados', '')

    return text

def get_news_corpus(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1', class_='typography__display--2').text
    subtitle = soup.find('div', class_='single__excerpt typography__body--2 spacing--mb4').text

    corpus = soup.find('div', class_='element-border--bottom spacing--pb4')
    corpus_text = []

    for p in corpus:
        corpus_text.append(p.text)
  
    corpus_text = "".join(corpus_text)

    text = f'{title}. {subtitle}. {corpus_text}'

    text = format_text(text)

    return text

def process_dataset(dataset, output_file='infomoney_news.csv', save_interval=100):
    dataset['text'] = None

    for index, row in dataset.iterrows():
      if pd.isnull(row['text']):
        try:
            news_text = get_news_corpus(row['urls'])
            dataset.loc[index, 'text'] = news_text
            print(f"Record {index} processed successfully")
        except ConnectionError as e:
            print(f"Connection error processing record {index}: {e}")
        except Exception as e:
            print(f"Error processing record {index}: {e}")
    return dataset


def tranform_timestamp_string(datafilm):
    data_list = list()
    for count in range(len(datafilm['data'])):
        data_list.append(datafilm.loc[count, 'data'].strftime('%d/%m/%Y'))
    datafilm['data'] = data_list
    return datafilm

def run(max_tweets = 500):
    datafilm = get_tweets(max_tweets)
    datafilm = get_url_from_text(datafilm)
    datafilm = process_dataset(datafilm)
    datafilm = tranform_timestamp_string(datafilm)
    datafilm.to_csv(r"\backend\Data\newsletter.csv")

run()
schedule.every().day.at("00:00:00").do(run)
while True:
    # Run the scheduled tasks
    schedule.run_pending()
    
    # Wait for 1 second before checking the schedule again
    time.sleep(1)