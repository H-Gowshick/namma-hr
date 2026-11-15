
from pydantic import BaseModel, ConfigDict


class TopicResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    difficulty: str
    summary: str
    features: list[str]
