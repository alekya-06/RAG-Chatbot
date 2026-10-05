import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in the .env file")

client = MongoClient(MONGODB_URI,compressors=["zlib"])

db: Database = client["rag_chatbot"]
movies: Collection = db["movies"]

def test_connection() -> None:
    client.admin.command("ping")
    print("MongoDB connection successful!")


if __name__ == "__main__":
    test_connection()