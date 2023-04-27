from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import redis
import json

app = FastAPI()
r = redis.Redis(host='localhost', port=6379)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Notice(BaseModel):
    notice: str


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
                return json.loads(message['data'])
            except:
                pass