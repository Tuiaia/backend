from pymongo import MongoClient
import redis
from bson.json_util import dumps, loads

class MongoDBHandler:
    
    def __init__(self, host = "localhost", port=27017, db_name="backendDb", collection_name="newsletter"):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        self.client = MongoClient(host=self.host, port=self.port)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
    
    def disconnect(self):
        self.client.close()
    
    def load_data(self):
        for doc in self.collection.find():
            yield dumps(doc)
    
    def save_data(self, data):
        if isinstance(data, list):
            self.collection.insert_many(data)
        elif isinstance(data, dict):
            self.collection.insert_one(data)
        else:
            raise TypeError("Data must be a list or a dictionary")

    def ScrapingHandler(self, message):
        received_dict = loads(message['data'])
        self.save_data(received_dict)

    def Newsletter(self):
        redis_conn = redis.Redis(host='localhost', port=6379)
        p = redis_conn.pubsub()
        p.subscribe(**{'canal_scraping': self.ScrapingHandler})
        p.subscribe(**{'canal_newsletter' : self.newsletterHandler})
        p.run_in_thread(sleep_time=0.001)

    def newsletterHandler(self, message):
        r = redis.Redis(host='localhost', port=6379)
        r.publish('canal_newsletterData', dumps(self.load_data()))

teste = MongoDBHandler()
teste.Newsletter()