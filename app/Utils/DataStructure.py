from pymongo import MongoClient
from bson.json_util import dumps
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

host = os.getenv("MONGO_HOST")
class MongoDBHandler:
    
    def __init__(self, host = host, port=27017, db_name="backendDb", collection_name="newsletter"):
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

class ScrapingHandler(MongoDBHandler):
    def __init__(self, host = host, port=27017, db_name="backendDb", collection_name="newsletter"):
        super().__init__(host, port, db_name, collection_name)

    def load_data(self, interval: dict):
        inicio = datetime.strptime(interval['inicio'], "%d/%m/%Y").date()
        fim = datetime.strptime(interval['fim'], "%d/%m/%Y").date()
        delta = fim - inicio
        for i in range(delta.days + 1):
            dia = inicio + timedelta(days=i)
            for doc in self.collection.find({'date' : dia.strftime("%d/%m/%Y")}):
                yield dumps(doc)
    
    def save_data(self, data):
        if isinstance(data, list):
            self.collection.insert_many(data)
        elif isinstance(data, dict):
            self.collection.insert_one(data)
        else:
            raise TypeError("Data must be a list or a dictionary")