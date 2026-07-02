import certifi
from pymongo import MongoClient

from config import DATABASE_NAME, MONGODB_URI

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set")

if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME is not set")

client = MongoClient(
    MONGODB_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
)
db = client[DATABASE_NAME]


def check_db_connection():
    client.admin.command("ping")
    return True
