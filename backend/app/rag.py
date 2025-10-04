# backend/app/rag.py
from __future__ import annotations
import os
import shutil
import hashlib
from typing import List, Tuple, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Google-only 크롤러
from .crawler_google import NaverNewsCrawler

load_dotenv()

# -----------------------------
# 설정(ENV로 오버라이드 가능)
# -----------------------------
_default_vs = os.path.abspath(
    os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(__file__), "..", "vectorstore"))
)
CHROMA_DIR = _default_vs
COLLECTION = os.getenv("COLLECTION", "news")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

CRAWL_DAYS = int(os.getenv("CRAWL_DAYS", "3"))
CRAWL_PAGES = int(os.getenv("CRAWL_PAGES", "1"))
RAG_HEADLESS = os.getenv("RAG_HEADLESS", "1") not in ("0", "false", "False")

MAX_LINKS = int(os.getenv("MAX_LINKS_PER_QUERY", "4"))
TIME_BUDGET_SEC = float(os.getenv("TIME_BUDGET_SEC", "30"))
MIN_CHARS = int(os.getenv("MIN_CHARS", "180"))

# -----------------------------
# 임베딩 (GPU/CPU 자동)
# -----------------------------
def _embeddings():
    import torch
    force_cpu = os.getenv("FORCE_CPU", "0") in ("1", "true", "True")
    device = "cuda" if (torch.cuda.is_available() and not force_cpu) else "cpu"
    print(f"[embeddings] device={device}, model={EMBED_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": device},
    )

# -----------------------------
# Chroma 영속화(버전 호환)
# -----------------------------
def _persist(vs) -> None:
    """Chroma/LC 버전 차이를 안전 처리."""
    try:
        vs.persist()  # type: ignore[attr-defined]
        return
    except Exception:
        pass
    try:
        vs._client.persist()  # type: ignore[attr-defined]
    except Exception:
        pass

# -----------------------------
# 벡터스토어(대화-ID별 분리)
# -----------------------------
def _vs(conversation_id: Optional[str] = None):
    if conversation_id:
        persist_dir = os.path.join(CHROMA_DIR, conversation_id)
        collection = f"{COLLECTION}__{conversation_id}"
    else:
        persist_dir = CHROMA_DIR
        collection = COLLECTION

    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=collection,
        embedding_function=_embeddings(),
        persist_directory=persist_dir,
    )

textsplitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)

def _make_id(url: str, content: str, i: int) -> str:
    h = hashlib.sha1()
    h.update(url.encode("utf-8"))
    h.update(b"::")
    h.update(content[:1024].encode("utf-8"))
    h.update(b"::")
    h.update(str(i).encode("utf-8"))
    return h.hexdigest()

# -----------------------------
# 크롤 → 청크 → 저장
# -----------------------------
def _fetch_and_store(
    query: str,
    days: int = CRAWL_DAYS,
    pages: int = CRAWL_PAGES,
    conversation_id: Optional[str] = None,
) -> int:
    from time import time
    start = time()
    saved = 0
    vs = _vs(conversation_id)

    with NaverNewsCrawler(headless=RAG_HEADLESS, max_pages=pages, debug=True) as cr:
        links: List[Tuple[str, str]] = cr.search_links(query, days=days, max_pages=pages)
        links = links[:MAX_LINKS]
        print(f"[rag] will process up to {len(links)} links")

        for (url, title) in links:
            if time() - start > TIME_BUDGET_SEC:
                print(f"[rag] crawl budget exceeded ({TIME_BUDGET_SEC:.1f}s). stop fetching more.")
                break

            body = cr.extract_article_text(url)
            if not body or len(body) < MIN_CHARS:
                print(f"[rag] skip (short {len(body) if body else 0} chars): {title} | {url}")
                continue

            chunks = textsplitter.split_text(body)
            docs: List[Document] = []
            ids: List[str] = []
            for i, ch in enumerate(chunks):
                meta = {"source": url, "title": title, "query": query}
                docs.append(Document(page_content=ch, metadata=meta))
                ids.append(_make_id(url, ch, i))

            if docs:
                vs.add_documents(documents=docs, ids=ids)
                _persist(vs)
                saved += len(docs)
                print(f"[rag] saved chunks: {len(docs)} (total {saved})")

    return saved

# -----------------------------
# 질의 → 검색 → (fast면 생략) → 필요 시 크롤
# -----------------------------
def answer_with_live(
    question: str,
    k: int = 4,
    fast: bool = False,
    conversation_id: Optional[str] = None,
) -> tuple[str, list[dict]]:
    vs = _vs(conversation_id)

    # 1) 검색
    retriever = vs.as_retriever(search_kwargs={"k": k})
    try:
        ctx_docs = retriever.invoke(question)
    except TypeError:
        ctx_docs = retriever.get_relevant_documents(question)

    # 2) fast=False일 때만 크롤
    if not ctx_docs and not fast:
        added = _fetch_and_store(
            question, days=CRAWL_DAYS, pages=CRAWL_PAGES, conversation_id=conversation_id
        )
        print(f"[rag] fetched_and_stored docs={added}")
        vs = _vs(conversation_id)
        retriever = vs.as_retriever(search_kwargs={"k": k})
        try:
            ctx_docs = retriever.invoke(question)
        except TypeError:
            ctx_docs = retriever.get_relevant_documents(question)

    # 3) 여전히 없으면 안내
    if not ctx_docs:
        msg = (
            "현재 저장된 문서가 없습니다. ‘빠른 검색(크롤 생략)’을 꺼두고 다시 시도해 보세요."
            if fast else
            "관련 기사 크롤/저장 결과가 0건입니다. 키워드를 더 구체적으로 입력해 주세요."
        )
        return (msg, [])

    # 4) 소스 요약
    sources = []
    for d in ctx_docs:
        src = d.metadata.get("source", "")
        title = d.metadata.get("title", "")
        preview = d.page_content[:220].replace("\n", " ")
        sources.append({"title": title, "url": src, "preview": preview})

    # 5) LLM
    context_block = "\n\n".join(
        f"[{i + 1}] {d.metadata.get('title', '')}\nURL: {d.metadata.get('source', '')}\n{d.page_content[:1200]}"
        for i, d in enumerate(ctx_docs)
    )
    prompt = (
        "다음 뉴스 문맥을 바탕으로 사용자의 질문에 한국어로 간결히 답하세요. "
        "출처 번호를 대괄호로 인용하세요(예: [1][2]). "
        "추측은 금지하고, 불확실하면 부족한 정보를 명확히 적으세요.\n\n"
        f"뉴스 문맥:\n{context_block}\n\n질문: {question}\n답변:"
    )

    try:
        from openai import OpenAI
        client = OpenAI()
        comp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        answer = comp.choices[0].message.content.strip()
    except Exception as e:
        answer = (
            "LLM 호출 중 오류가 발생했습니다. OPENAI_API_KEY / MODEL_NAME 환경변수를 확인해 주세요.\n"
            f"세부: {e}"
        )

    return answer, sources

# -----------------------------
# 보조 유틸
# -----------------------------
def vector_stats() -> dict:
    vs = _vs()
    out = {"collection": COLLECTION, "persist_dir": CHROMA_DIR}
    try:
        n = vs._collection.count()  # type: ignore[attr-defined]
    except Exception:
        try:
            n = len(vs.get()["ids"])
        except Exception:
            n = 0
    out["count"] = int(n)
    return out

def debug_fetch_links(
    q: str,
    days: int = CRAWL_DAYS,
    pages: int = 1,
    headless: bool | None = None,
) -> list[tuple[str, str]]:
    use_headless = RAG_HEADLESS if headless is None else bool(headless)
    with NaverNewsCrawler(headless=use_headless, max_pages=pages, debug=True) as cr:
        links = cr.search_links(q, days=days, max_pages=pages)
    return links

# 벡터스토어 전체/대화별 초기화
def clear_vectorstore(conversation_id: Optional[str]) -> int:
    target = os.path.join(CHROMA_DIR, conversation_id) if conversation_id else CHROMA_DIR
    if not os.path.exists(target):
        return 0
    root = os.path.abspath(CHROMA_DIR)
    tgt = os.path.abspath(target)
    if not tgt.startswith(root):
        return 0
    shutil.rmtree(tgt, ignore_errors=True)
    return 1
