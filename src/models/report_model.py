from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from src.database.index import db


class Report(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: ObjectId
    repository_id: ObjectId
    summary: str = Field(..., min_length=1)
    tech_stack: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


reports = db["reports"]
