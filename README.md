# 📱 Live RAG 뉴스 검색

 “질문 → 최신 뉴스 크롤링 → 벡터DB 저장/검색 → LLM 답변”까지 한 번에 처리하는 **Live RAG(저장·검색 증강) 웹앱**입니다. 
  <br>
  프론트(React + Vite), 백엔드(FastAPI), 임베딩(HuggingFace), 벡터스토어(Chroma), LLM(OpenAI)로 구성했으며            
  <br>
  **대화 세션 분리, 빠른/정확 모드, 타임아웃 가드, 크롤링 실패 대비(fallback)를** 갖춘 실전형 구조입니다. 

<br>

## ✨ 주요 기능

<details>
  
  <summary>주요 기능</summary>

  - **Live RAG**: 질문 시 관련 뉴스를 **실시간 크롤링 → 문서 청크 → 임베딩 → Chroma 저장/검색 → LLM 답변**
  - **구글 뉴스 기반 크롤러**: Google News **RSS → HTML 순서**로 검색, 본문은 **Trafilatura → Selenium** 순으로 추출 (빠름+안정성)
  - **세션 격리**: 프론트에서 **conversationId**를 부여하면, 백엔드가 **세션별 벡터스토어 디렉터리/컬렉션**을 분리해 문맥이 섞이지 않음
  - **빠른 검색(크롤 생략):** 기존에 쌓인 벡터만 검색하여 **응답 지연/타임아웃 방지**
  - **시간·링크 예산:** TIME_BUDGET_SEC, MAX_LINKS 로 크롤링 비용 통제
  - **타임아웃/오류 핸들링:** 프런트 30–60s 타임아웃, 백엔드에서 오류를 **200 응답 + 메시지**로 돌려 UI가 사용자 친화적으로 표시
  - **CORS/환경변수:** 로컬·배포 환경 전환을 .env로 관리
  - **LangChain 경량 사용:** 거대한 체인 대신 **Text Splitter / Embeddings / Chroma 래퍼 / Retriever**만 사용

  <br>
</details>



## ⚙️ 사양(개발 환경) 및 기술 스택

<details>
  <summary>사양(개발 환경) 및 기술 스택</summary>

  ### 사양
  - **OS:** WINDOWS 11 PRO EDITION
  - **CPU:** AMD RYZEN 5 9600X
  - **RAM:** DDR5 32G
  - **GPU:** NVIDIA RTX 4070TI SUPER
  - **Python:** 3.11
  - **Node:** v22.20.0
  - **Chrome:** 최신 (Selenium용)

  ### 기술 스택
  - **Frontend:** React + Vite + TypeScript + TailwindCSS
  - **Backend:** FastAPI + Uvicorn
  - **RAG:**
    - **크롤링:** Google News RSS/HTML, Trafilatura(HTTP 우선), Selenium(폴백)
    - **임베딩:** HuggingFace sentence-transformers/all-MiniLM-L6-v2 (CUDA 있으면 자동 GPU)
    - **벡터스토어:** Chroma (세션별 persist 디렉토리)
    - **LLM:** OpenAI Chat Completions (기본 gpt-4o-mini)
  - **Infra/기타:** Python 3.11, Node 22+, CUDA, WebDriver Manager
    
 <br>
</details>

## 🗂 프로젝트 구조

<details>
  <summary>프로젝트 구조</summary>

  
  ```bash
  llm_rag_project/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                # FastAPI 엔드포인트 (health, query, vector/stats, debug/crawl)
│  │  ├─ rag.py                 # Live RAG 로직 (세션 분리, 크롤→임베딩→저장→검색→LLM)
│  │  ├─ crawler_google.py      # Google News RSS/HTML + Trafilatura + Selenium
│  │  ├─ schemas.py             # Pydantic 스키마 (QueryRequest/Response, CrawlReq 등)
│  │  └─ __init__.py
│  ├─ vectorstore/              # (세션별) Chroma persist 디렉토리
│  ├─ .env                      # 백엔드 환경변수
│  └─ requirements.txt
└─ frontend/
   ├─ src/
   │  ├─ api.ts                 # Axios 클라이언트, BASE_URL, ask(), clear()
   │  └─ App.tsx                # UI (질문/Top-k/빠른검색, 새 채팅, 응답/참고문서)
   ├─ .env.local                # 프론트 환경변수 (VITE_API_BASE 등)
   ├─ index.html, tailwind.css, package.json, vite.config.ts

  ```
<br>
</details>

## 🔑 환경 변수

<details>
  <summary>환경 변수</summary>

  
  ### backend/.env
   ```env
OPENAI_API_KEY=sk-proj...             # OpenAI 키
MODEL_NAME=gpt-4o-mini                # 또는 gpt-4o, gpt-4.1 등
CHROMA_DIR=./vectorstore
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
ALLOWED_ORIGINS=http://localhost:5173

# --- 권장: 속도/안정성 ---
CRAWL_DAYS=3
CRAWL_PAGES=1
MAX_LINKS_PER_QUERY=4
TIME_BUDGET_SEC=30
MIN_CHARS=180
   ```


### frontend/.env.local
```env
VITE_API_BASE=http://127.0.0.1:8000
VITE_REQUEST_TIMEOUT=30000
```
</details>


## 🚀 실행 방법

<details>
  <summary>실행 방법</summary>
  
  ```env
# 1) 백엔드
cd backend
python -m venv .venv && . .venv/Scripts/activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 2) 프론트엔드
cd ../frontend
npm i
npm run dev
# 브라우저: http://localhost:5173
  ```
</details>


## 🧭 동작 흐름 (시퀀스 다이어그램)

<details>
  <summary>동작 흐름 (시퀀스 다이어그램)</summary>

  <img width="3840" height="2225" alt="Untitled diagram _ Mermaid Chart-2025-10-05-140332" src="https://github.com/user-attachments/assets/46d5d39d-37ab-44ba-a5bd-e3a04106f3f5" />

</details>


## 🔎 LangChain 사용 범위 (경량)

<details>
  <summary>LangChain 사용 범위 (경량)</summary>

  
  - **langchain_huggingface.HuggingFaceEmbeddings:** MiniLM 임베딩
  - **langchain_text_splitters.RecursiveCharacterTextSplitter:** 청크
  - **langchain_chroma.Chroma:** 벡터스토어 래퍼
  - **as_retriever().invoke():** Top-k 검색

   LLM 호출은 OpenAI SDK로 직접 수행(에이전트/체인 미사용 → 간결/예측가능/디버깅 쉬움)
    <br>
</details>

## 📈 성능/정확도 전략

<details>
  <summary>성능/정확도 전략</summary>

  - **정확도:** RSS 우선(정규화 링크/제목) → HTML 폴백, Trafilatura 본문 추출(정확/경량) → Selenium 폴백. <br>
답변 프롬프트는 **출처 번호 인용**을 강제해 환각 감소.
- **성능:** 링크/시간 예산으로 크롤 비용 제한, 임베딩 GPU 자동 사용, 세션별 벡터스토어로 검색 범위 축소, 프론트 “빠른 검색” 토글 제공.

  <br>
</details>

## 🖼️ 스크린샷

<details>
  <summary>스크린샷</summary>

  ### 시작 화면
  <img width="1712" height="1263" alt="image" src="https://github.com/user-attachments/assets/eff698e5-ecef-4281-8bbd-cceb48dd01ae" />

  ### 실행 화면
  <img width="1714" height="1264" alt="image" src="https://github.com/user-attachments/assets/5cc27109-dd33-4b48-a467-e307af6e062c" />

</details>

<br><br>

## 🤕 어려웠던 점 & 해결 방법

<details>
  <summary>1. PowerShell에서 `curl` JSON 깨짐 / 400·500 에러</summary>

- **증상**: `curl -d "{...}"` 호출 시 한글/따옴표가 깨지거나 `JSON decode error`, 포트 오류 메시지.
- **원인**: PowerShell의 이스케이프 규칙/인코딩 차이. 작은따옴표·줄바꿈/백틱 조합이 깨짐.
- **해결**
  - PowerShell 대안:
    ```powershell
    python -c "import requests; print(requests.post('http://127.0.0.1:8000/query', json={'question':'트럼프','k':4}, timeout=60).text)"
    ```
  - 또는 `-d @body.json` 방식 사용.
- **예방**: 로컬 테스트는 `requests` 파이썬 원라이너 권장. 프론트에서 직접 호출 우선.

  <br>
</details>

<details>
  <summary>2. 본문 추출 실패로 저장 0건 (crawl budget exceeded)</summary>

- **증상**: `fetched_and_stored docs=0`, `skip (short 0 chars)` 로그.
- **원인**: 일부 사이트에서 Trafilatura가 본문을 못 뽑거나, 로딩 지연으로 Selenium이 텍스트를 못 가져옴.
- **해결**
  - 추출 순서: **Trafilatura(HTTP) → Selenium 폴백**
  - 셀렉터 후보 확장: `#dic_area, article, #newsct, .article_body, #articleBody ...`
  - `MAX_LINKS_PER_QUERY`를 늘리되 `TIME_BUDGET_SEC` 내에서만 처리.
- **예방**: 뉴스 소스 다양화(동일 쿼리라도 링크 여러 개 시도), 환경에 맞춰 시간 예산 튜닝.

  <br>
</details>

<details>
  <summary>3. 타임아웃/응답 지연 (`timeout of 30000ms exceeded`)</summary>

  - **증상**: 프론트에서 30초 타임아웃.
- **원인**: 초기 크롤+본문 추출+임베딩이 느림(특히 Selenium 폴백).
- **해결**
  - 프론트 `.env.local`: `VITE_REQUEST_TIMEOUT=60000` (필요 시 ↑)
  - 백엔드 `.env`: `MAX_LINKS_PER_QUERY`↓, `CRAWL_PAGES=1`, `TIME_BUDGET_SEC=15~20`
  - UI에서 **“빠른 검색(크롤 생략)”** 제공.
- **예방**: 크롤은 비용 큼 — 링크/시간 예산 **보수적** 운영.

  <br>
</details>

<details>
  <summary>4. Pydantic 검증 실패 (contexts 타입)</summary>

  - **증상**: `QueryResponse` 검증 오류: `contexts[i]` string 요구인데 dict 전달.
- **원인**: 스키마와 실제 응답 구조 불일치.
- **해결**: 스키마를 `List[ContextItem]`(title/url/preview)로 정의하고 반환 데이터 구조 통일.
- **예방**: 프론트/백 스키마를 **단일 소스**로 관리(예: `schemas.ts/json schema`).

  <br>
</details>

<details>
  <summary>5. 세션(대화) 간 문맥 섞임</summary>

  - **증상**: “새 채팅”을 눌러도 이전 주제 문맥이 섞여 보임.
- **원인**: 같은 Chroma 컬렉션/디렉터리를 공유.
- **해결**: 요청마다 `conversationId`를 포함 → 백엔드가 **세션별 persist dir/collection** 사용.
- **예방**: 새 채팅 시 UUID 발급 → 프론트 상태에 보관 → 모든 요청에 포함.

  <br>
</details>

<details>
  <summary>6. 벡터스토어 초기화 필요</summary>

  - **증상**: 오래된 문맥이 남아 이상 응답.
- **해결**: `vectorstore/`를 세션별로 분리하고, 필요시 **세션별 삭제** 유틸 제공.
- **예방**: 포트폴리오 데모에서는 “새 채팅” 시 **새 세션 디렉터리**를 사용.

  <br>
</details>

<br><br>

## 🙌 느낀점 & 배운점

<details>
  <summary>느낀점 & 배운점</summary>

<br>

처음엔 “일단 되게 하자”였는데, 금방 깨달았습니다. 한 번 되는 것보다 **항상 같은 품질로 되는 것**이 훨씬 어렵고 더 중요했습니다. 
크롤링도 RSS → HTML → Selenium 순서로 단계화하고, 링크 개수나 시간 예산을 걸어 두면서 흐름을 안정시키는 데 집중했습니다.

GPU도 처음엔 꼭 써야 한다고 생각했는데, 막상 소형 임베딩 모델에선 **CPU도 충분**했습니다. 게다가 환경 따라 GPU 초기화가 더 느릴 때도 있었습니다.  
그래서 FORCE_CPU 같은 스위치를 넣고, 어떤 디바이스를 쓰는지 로그로 남기면서 “왜 오늘은 느리지?” 같은 불확실성을 줄였습니다.

브라우저 드라이버가 뿜는 경고(QUOTA_EXCEEDED, DEPRECATED_ENDPOINT, WebGL 관련) 때문에 한동안 괜히 불안했는데, **결국 치명적인 에러는 아니었다**는 걸 확인했습니다. 
중요한 건 콘솔 색깔이 아니라, 요청 → 검색 → 본문 추출 → 임베딩 → 답변까지 그 **파이프라인 실행 유무**였습니다.

PowerShell에서 cURL로 JSON 보낼 때 이스케이프가 계속 깨졌습니다. 쉘마다 규칙이 다르다는 걸 다시 배웠고, 문서에는 **셸·언어별 예시**를 따로 준비하는 게 사용자(또는 동료) 경험에 진짜 중요하다는 걸 체감했습니다.

스키마 정합성은 백엔드는 contexts: List[dict]로 내보내는데, 모델은 List[str]로 정의돼 있어서 검증 에러가 났습니다.. 그 뒤로는 **응답 모델과 실제 페이로드를 항상 1:1**로 맞추고, 혹시 모를 상황에 대비해 런타임에서도 방어적으로 캐스팅하는 습관을 들였습니다.

Chroma는 버전에 따라 persist() 유무가 달라서 당황했는데, 폴리필 헬퍼를 하나 두고 persist() → _client.persist() → (없으면 패스) 순서로 처리하니 안정됐습니다. **데이터 계층은 느슨하게 결합**해두는 게 결국 유지보수에 유리하다는 걸 실감했습니다.

“빠른 검색(크롤 생략)” 토글은 단순한 옵션처럼 보이지만, 실제로는 **속도 vs 정확성**을 사용자가 직접 선택하게 하는 장치였습니다. 저는 기본을 정확성(크롤 ON)으로 두고, 필요할 때만 빠르게 스위치하도록 했습니다. 

질문 문맥이 섞이는 문제는 **conversationId로 세션별 컬렉션을 분리**해서 풀었습니다. “새 채팅”을 눌렀는데 이전 주제가 묻어나오면 신뢰가 깨지거든요. 격리하고 나니 혼선이 눈에 띄게 줄었습니다.

무엇보다, **신뢰는 출처에서 온다**는 걸 다시 배웠습니다. 답변이 조금 느려도, 근거가 보이면 사용자가 훨씬 편안해합니다. 그래서 타이틀/URL/프리뷰를 카드로 보여 주고, 본문엔 [1][2]처럼 인용을 달게 했습니다. 

타임아웃도 큰 깨달음이었습니다. 무한 대기는 느림이 아니라 **불안**으로 느껴집니다. 서버와 프런트에 명확한 시간 제한을 두고, 시간이 초과되면 지금까지의 수집 결과로라도 답변을 주니 품질을 높아졌습니다.

멋진 기능 하나보다, **작게라도 매번 같은 품질로 끝까지 가는 시스템**이 더 가치 있습니다. 계층적 폴백, 리소스 예산, 타입 정합성, 세션 격리, 출처 노출… 이 기본기들을 차근히 챙겼더니, 제품이 안정적으로 서비스를 유지했습니다.. 
저는 그 과정을 통해, 모델 공부 만큼이나 **시스템을 다루는 감각이 중요**하다는 걸 배웠습니다.
  
</details>






