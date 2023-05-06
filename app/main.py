from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
from app.Scraping.BoraInvestir import BoraInvestir
from app.Scraping.Forbes import Forbes
from app.DataStructure import MongoDBHandler
from fastapi_utils.tasks import repeat_every

app = FastAPI()
r = redis.Redis(host='redis', port=6379)

class classifyDTO(BaseModel):
    classificacao: int
    probabilidade: float

class Notice(BaseModel):
    notice: str

@app.on_event("startup")
@repeat_every(seconds = 10)
def get_feed():
    r.publish('canal_feed', 0)

def get_mongodb(): 
    teste = MongoDBHandler()
    teste.Newsletter()

def get_news():
    Forbes().run()
    BoraInvestir().run()

get_mongodb()
get_news()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/')
async def classify(notice: Notice):
    return notice.notice

@app.get('/newsletter')
async def newsletter():
    r.publish('canal_newsletter', "get_news")
    pubsub = r.pubsub()
    pubsub.subscribe('canal_newsletterData')
    for message in pubsub.listen():
        if message['data'] != 1:
            try:
                return [json.loads(x) for x in json.loads(message['data'])]
            except:
                pass