from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from config import DATABASE_NAME, MONGODB_URI

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set")

if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME is not set")

try:
    client = MongoClient(MONGODB_URI)
    client.admin.command("ping")
    db = client[DATABASE_NAME]
    print("MongoDB connected successfully!")

except ConnectionFailure as exc:
    raise ConnectionFailure("Failed to connect to MongoDB") from exc

except Exception as exc:
    raise RuntimeError("Unexpected error while connecting to MongoDB") from exc
