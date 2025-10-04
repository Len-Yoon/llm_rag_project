# backend/app/main.py
import os, traceback
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .schemas import QueryRequest, QueryResponse, CrawlReq, ClearReq, Source
from .rag import answer_with_live, vector_stats, debug_fetch_links, clear_vectorstore

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]

app = FastAPI(title="FinNews Live-RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/vector/stats")
def vector_stats_ep():
    return vector_stats()

@app.post("/vector/clear")
def vector_clear_ep(req: ClearReq):
    n = clear_vectorstore(req.conversation_id)
    return {"cleared": n}

@app.get("/debug/crawl")
def debug_crawl_get(
    q: str = Query(..., description="검색어"),
    days: int = Query(3, ge=1, le=30, description="최근 n일"),
    pages: int = Query(1, ge=1, le=5, description="페이지 수"),
    headless: bool = Query(True, description="헤드리스 여부"),
):
    try:
        links = debug_fetch_links(q, days=days, pages=pages, headless=headless)
        return {"count": len(links), "links": links[:20]}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/debug/crawl")
def debug_crawl_post(req: CrawlReq):
    try:
        links = debug_fetch_links(req.q, days=req.days, pages=req.pages, headless=req.headless)
        return {"count": len(links), "links": links[:20]}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        ans, ctx = answer_with_live(
            req.question, k=req.k, fast=req.fast, conversation_id=req.conversation_id
        )
        # pydantic 모델로 맞춰줌
        sources = [Source(**s) for s in ctx]
        return QueryResponse(answer=ans, contexts=sources)
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "answer": "서버 내부 오류가 발생했습니다. 로그/환경설정을 확인해주세요.",
                "contexts": [],
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
