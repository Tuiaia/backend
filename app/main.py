from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from app.Utils.RedisConnection import redisConnection
from app.Utils.channelParameters import channel
redis = redisConnection()

app = FastAPI()

class News(BaseModel):
    news: str

@app.on_event("startup")
@repeat_every(seconds = 7200)
def get_feed():
    redis.r.publish(channel['forbes'], 0)
    redis.r.publish(channel['b3'], 0)



@app.on_event("startup")
def run_connections():
    redis.run_mongo()
    redis.run_scraping()
    redis.run_classifer()

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
async def newsletter():
    return redis.get_newsletter()
    