from datetime import datetime
from typing import Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from src.database.index import db


class Chat(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: ObjectId
    repository_id: ObjectId
    role: Literal["user", "assistant", "system"]
    message: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


chats = db["chats"]
