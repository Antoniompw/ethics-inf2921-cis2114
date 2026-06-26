from pydantic import BaseModel

class AskRequest(BaseModel):
    question: str
    source: str | None = None
    k: int = 3


class Citation(BaseModel):
    source: str
    page: int
    distance: float


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]