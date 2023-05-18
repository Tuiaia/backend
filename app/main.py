from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from app.Utils.RedisConnection import redisConnection
from app.Utils.channelParameters import channel
from datetime import datetime
from fastapi.responses import StreamingResponse
from app.Dashboard.wordcloud_generator import WordCloudGenerator
import io

redis = redisConnection()

app = FastAPI()

wordcloud_generator = WordCloudGenerator()


class News(BaseModel):
    news: str


@app.on_event("startup")
@repeat_every(seconds=30)
def get_feed():
    redis.r.publish(channel['forbes'], 0)
    redis.r.publish(channel['b3'], 0)
    redis.r.publish(channel['googleNews'], 0)


@app.on_event("startup")
def run_connections():
    redis.run_mongo()
    redis.run_scraping()
    redis.run_classifer()
    redis.run_feedclassifer()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/')
async def classify(news: News):
    return redis.get_classifier(news.news)


@app.get('/feed')
async def newsletter(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                     enddate: str = datetime.today().strftime("%d/%m/%Y")):
    return redis.get_newsletter({'inicio': startdate, 'fim': enddate})


@app.get('/wordcloud', response_class=StreamingResponse)
async def get_wordcloud(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                        enddate: str = datetime.today().strftime("%d/%m/%Y")):
    news = redis.get_newsletter({'inicio': startdate, 'fim': enddate})
    news_text = [x['title'] for x in news]
    text = ' '.join(news_text)  # TODO: adaptar para concatenar todos os textos das notícias
    wordcloud = wordcloud_generator.generate_wordcloud(text)
    image_bytes = wordcloud_generator.get_wordcloud_image(wordcloud)

    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")

@app.get('/barwordcloud', response_class=StreamingResponse)
async def get_wordcloud(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                        enddate: str = datetime.today().strftime("%d/%m/%Y")):
    news = redis.get_newsletter({'inicio': startdate, 'fim': enddate})
    news_text = [x['title'] for x in news]
    text = ' '.join(news_text)  # TODO: adaptar para concatenar todos os textos das notícias
    return StreamingResponse(io.BytesIO(wordcloud_generator.get_bar_graph(text)), media_type="image/png")