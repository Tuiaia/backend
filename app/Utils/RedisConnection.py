import redis
from bson.json_util import dumps, loads
import json
from app.Utils.DataStructure import ScrapingHandler
from dotenv import load_dotenv
import os
from app.Utils.channelParameters import channel
import uuid

load_dotenv()
# Load the Redis host from the environment variables
host = os.getenv("REDIS_HOST")
# Instantiate the MongoDB ScrapingHandler
MongoScraping = ScrapingHandler()
class redisConnection:
    def __init__(self, host = host, port = 6379):
        self.r = redis.Redis(host=host, port=port, db=0)


    def get_newsletter(self, interval: dict):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Publish the request to the feedTransmitter channel with the request ID and interval as JSON
        self.r.publish(channel["feedTransmitter"], f"{request_id}:!&{dumps(interval)}")

        # Subscribe to the request ID channel
        pubsub = self.r.pubsub()
        pubsub.subscribe(request_id)

        # Listen for messages on the request ID channel
        for message in pubsub.listen():
            if message['data'] != 1:
                try:
                    pubsub.unsubscribe(request_id)

                    # Return the retrieved newsletters as a list of dictionaries
                    return [json.loads(x) for x in json.loads(message['data'])]
                except:
                    pass
                
    def get_classifier(self, notice: str):
        # Similar logic as get_newsletter method
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

    def get_feedClassifier(self, notice: str):
        # Similar logic as get_newsletter method
        request_id = str(uuid.uuid4())
        self.r.publish(channel["classifyFeedTransmitter"], f"{request_id}:!&{dumps(notice)}")
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
        # Run the classifier logic using a separate class
        from app.AI.classifier import Classifier
        p = self.r.pubsub()
        classify = Classifier()
        p.subscribe(**{channel['classifyTransmitter']: classify.classify_text})
        p.run_in_thread(sleep_time=0.001)

    def run_feedclassifer(self):
        # Run the feed classifier logic using a separate class
        from app.AI.feedClassifier import feedClassifier
        p = self.r.pubsub()
        classify = feedClassifier()
        p.subscribe(**{channel['classifyFeedTransmitter']: classify.classify_text})
        p.run_in_thread(sleep_time=0.001)

    def run_scraping(self):
        # Run the scraping logic for different sources using separate classes
        from app.Scraping.BoraInvestir import BoraInvestir
        from app.Scraping.Forbes import Forbes
        from app.Scraping.GoogleNews import GoogleNews
        p= self.r.pubsub()
        p.subscribe(**{channel["forbes"] : Forbes().get_urls})
        p.subscribe(**{channel["b3"] : BoraInvestir().get_urls})
        p.subscribe(**{channel["googleNews"] : GoogleNews().get_urls})
        p.run_in_thread(sleep_time=0.001)


    def run_mongo(self):
        # Subscribe to channels and handle messages for saving data and handling newsletters
        p = self.r.pubsub()
        p.subscribe(**{channel['saveData']: self.ScrapingHandler})
        p.subscribe(**{channel['feedTransmitter'] : self.newsletterHandler})
        p.run_in_thread(sleep_time=0.001)

    def newsletterHandler(self, message):
        # Handle the incoming message for newsletter retrieval
        request_id, text = self.separate_id_text(message['data'])
        self.r.publish(request_id, dumps(MongoScraping.load_data(text)))

    def ScrapingHandler(self, message):
        # Handle the incoming message for saving scraped data
        received_dict = loads(message['data'])
        MongoScraping.save_data(received_dict)

    def separate_id_text(self, rawText):
        # Separate the request ID and data from the raw message
        text = rawText.split(b":!&")
        return text[0].decode('UTF-8'), json.loads(text[1])
