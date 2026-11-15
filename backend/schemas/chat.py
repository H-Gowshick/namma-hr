from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AppLanguageCode = Literal[
    "en",
    "hi",
    "ta",
    "te",
    "kn",
    "ml",
    "bn",
    "mr",
    "gu",
]


class chatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str


class chatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: list[chatMessage]
    language: AppLanguageCode = Field(
        default="en",
        description="UI language selected by the employee.",
    )
