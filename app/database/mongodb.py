from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("DB_NAME")]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def close(self):
        self.client.close()

def get_database():
    db_instance = MongoDB()
    try:
        yield db_instance.db
    finally:
        db_instance.close()