import redis
from bson.json_util import dumps, loads
import json
from app.Utils.DataStructure import ScrapingHandler
from dotenv import load_dotenv
import os
from app.Utils.channelParameters import channel
import uuid
load_dotenv()

host = os.getenv("REDIS_HOST")
MongoScraping = ScrapingHandler()
class redisConnection:
    def __init__(self, host = host, port = 6379):
        self.r = redis.Redis(host=host, port=port, db=0)


    def get_newsletter(self, interval: dict):
        request_id = str(uuid.uuid4())
        self.r.publish(channel["feedTransmitter"], f"{request_id}:!&{dumps(interval)}")
        pubsub = self.r.pubsub()
        pubsub.subscribe(request_id)
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
                    pubsub.unsubscribe(request_id)
                    return [json.loads(x) for x in json.loads(message['data'])]
                except:
                    pass
                
    def get_classifier(self, notice: str):
        request_id = str(uuid.uuid4())
        self.r.publish(channel["classifyTransmitter"], f"{request_id}:!&{dumps(notice)}")
        pubsub = self.r.pubsub()
        pubsub.subscribe(request_id)
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
                    pubsub.unsubscribe(request_id)
                    return json.loads(message['data'])
                except:
                    pass

    def run_classifer(self):
        from app.AI.classifier import Classifier
        p = self.r.pubsub()
        classify = Classifier()
        p.subscribe(**{channel['classifyTransmitter']: classify.classify_text})
        p.run_in_thread(sleep_time=0.001)


    def run_scraping(self):
        from app.Scraping.BoraInvestir import BoraInvestir
        from app.Scraping.Forbes import Forbes
        p= self.r.pubsub()
        p.subscribe(**{channel["forbes"] : Forbes().get_urls})
        p.subscribe(**{channel["b3"] : BoraInvestir().get_urls})
        p.run_in_thread(sleep_time=0.001)


    def run_mongo(self):
        p = self.r.pubsub()
        p.subscribe(**{channel['saveData']: self.ScrapingHandler})
        p.subscribe(**{channel['feedTransmitter'] : self.newsletterHandler})
        p.run_in_thread(sleep_time=0.001)

    def newsletterHandler(self, message):
        request_id, text = self.separate_id_text(message['data'])
        self.r.publish(request_id, dumps(MongoScraping.load_data(text)))

    def ScrapingHandler(self, message):
        received_dict = loads(message['data'])
        MongoScraping.save_data(received_dict)

    def separate_id_text(self, rawText):
        text = rawText.split(b":!&")
        return text[0].decode('UTF-8'), json.loads(text[1])
