import redis
from bson.json_util import dumps, loads
import json
from app.Utils.DataStructure import ScrapingHandler
from dotenv import load_dotenv
import os
from app.Utils.channelParameters import channel
load_dotenv()

host = os.getenv("REDIS_HOST")
MongoScraping = ScrapingHandler()
class redisConnection:
    def __init__(self, host = host, port = 6379):
        self.r = redis.Redis(host=host, port=port, db=0)


    def get_newsletter(self):
        self.r.publish(channel["feedTransmitter"], 0)
        pubsub = self.r.pubsub()
        pubsub.subscribe(channel["feedReceiver"])
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
                    return [json.loads(x) for x in json.loads(message['data'])]
                except:
                    pass
                
    def get_classifier(self, notice: str):
        self.r.publish(channel["classifyTransmitter"], dumps(notice))
        pubsub = self.r.pubsub()
        pubsub.subscribe(channel['classifyReceiver'])
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
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
        self.r.publish(channel['feedReceiver'], dumps(MongoScraping.load_data()))

    def ScrapingHandler(self, message):
        received_dict = loads(message['data'])
        MongoScraping.save_data(received_dict)

    
