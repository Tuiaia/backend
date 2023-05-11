from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from app.Utils.RedisConnection import redisConnection

redis = redisConnection()

app = FastAPI()

class Notice(BaseModel):
    notice: str

@app.on_event("startup")
@repeat_every(seconds = 7200)
def get_feed():
    redis.r.publish('canal_feed', 0)

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
async def classify(notice: Notice):
    return redis.get_classifier(notice.notice)



@app.get('/newsletter')
async def newsletter():
    return redis.get_newsletter()
    