import os
from dotenv import load_dotenv

load_dotenv()


def parse_expire_minutes(value: str) -> int:
    value = value.strip().lower()
    if value.endswith("d"):
        return int(value[:-1]) * 24 * 60
    if value.endswith("h"):
        return int(value[:-1]) * 60
    if value.endswith("m"):
        return int(value[:-1])
    return int(value)


JINA_API_KEY = os.getenv("JINA_API_KEY")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")
ACCESS_TOKEN_EXPIRE_MINUTES = parse_expire_minutes(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
