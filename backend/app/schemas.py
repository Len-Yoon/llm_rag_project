# backend/app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    k: int = 4
    fast: bool = False
    conversation_id: Optional[str] = None

class Source(BaseModel):
    title: Optional[str] = None
    url: str
    preview: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    contexts: List[Source]

class CrawlReq(BaseModel):
    q: str
    days: int = 3
    pages: int = 1
    headless: bool = True

class ClearReq(BaseModel):
    conversation_id: Optional[str] = None
