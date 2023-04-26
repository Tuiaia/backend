from pymongo import MongoClient

class MongoDBHandler:
    
    def __init__(self, host = "0.0.0.0", port="27017", db_name="backendDb", collection_name="newsletter"):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self):
        self.client = MongoClient(host=self.host, port=self.port)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
    
    def disconnect(self):
        self.client.close()
    
    def load_data(self):
        data = []
        for doc in self.collection.find():
            data.append(doc)
        return data
    
    def save_data(self, data):
        if isinstance(data, list):
            self.collection.insert_many(data)
        elif isinstance(data, dict):
            self.collection.insert_one(data)
        else:
            raise TypeError("Data must be a list or a dictionary")
