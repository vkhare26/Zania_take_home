from pydantic import BaseModel
from typing import List

class QARequest(BaseModel):
    questions: List[str]

class QAResponseItem(BaseModel):
    question: str
    answer: str
