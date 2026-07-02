import certifi
from pymongo import MongoClient

from config import DATABASE_NAME, MONGODB_URI

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set")

if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME is not set")


def get_mongo_client():
    # Atlas connection
    if MONGODB_URI.startswith("mongodb+srv://"):
        return MongoClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
        )

    # Local MongoDB / Compass connection
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )


client = get_mongo_client()
db = client[DATABASE_NAME]


def check_db_connection():
    client.admin.command("ping")
    return True