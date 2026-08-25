import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)
db = client["dailydrop"]

client.admin.command("ping")
print("연결 성공")
