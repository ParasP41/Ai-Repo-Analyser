from datetime import datetime
from typing import Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from src.database.index import db


class Repository(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: ObjectId
    repo_name: str = Field(..., min_length=1, max_length=100)
    github_url: str = Field(..., min_length=1)
    local_path: str = Field(..., min_length=1)
    branch: str = Field(default="main", min_length=1)
    language: str = Field(..., min_length=1)
    status: Literal["pending", "indexing", "indexed", "failed"] = "indexed"
    indexed_at: datetime = Field(default_factory=datetime.utcnow)


repositories = db["repositories"]
