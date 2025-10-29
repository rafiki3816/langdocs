# 🌟 Solar API 사용 분석 및 RAG 처리 과정

## 📋 목차
1. [개요](#개요)
2. [Solar API 사용 현황](#solar-api-사용-현황)
3. [RAG 시스템 처리 과정](#rag-시스템-처리-과정)
4. [상세 처리 플로우](#상세-처리-플로우)
5. [시스템 아키텍처](#시스템-아키텍처)
6. [코드 예시](#코드-예시)
7. [API 호출 시점](#api-호출-시점)
8. [최적화 포인트](#최적화-포인트)

---

## 개요

LangChain RAG 챗봇 시스템은 Upstage의 Solar API를 핵심 AI 엔진으로 사용합니다. Solar API는 두 가지 주요 기능을 제공합니다:
1. **Language Model (LLM)**: 답변 생성 및 텍스트 처리
2. **Embedding Model**: 문서와 질문의 벡터화

---

## Solar API 사용 현황

### 1. Language Model (LLM)

#### 1.1 일반 답변 생성
- **파일**: `llm.py`
- **모델**: `solar-pro` 또는 `solar-1-mini-chat`
- **함수**: `get_llm()`
- **설정**:
  ```python
  model = "solar-pro"
  temperature = 0.1  # 낮은 값으로 정확성 중시
  max_tokens = 2000
  streaming = False
  ```
- **용도**:
  - 사용자 질문에 대한 최종 답변 생성
  - RAG 컨텍스트 기반 응답 생성
  - 대화 메모리 기반 연속 대화 처리

#### 1.2 SQL 쿼리 생성
- **파일**: `text_to_sql.py`
- **모델**: `solar-pro`
- **함수**: `get_sql_llm()`
- **설정**:
  ```python
  model = "solar-pro"
  temperature = 0.0  # 완전 결정적 출력
  max_tokens = 1000
  streaming = False
  ```
- **용도**: 자연어를 SQL 쿼리로 변환

### 2. Embedding Model

#### 2.1 문서 임베딩
- **파일**: `llm.py`
- **모델**: `solar-embedding-1-large`
- **함수**: `get_embeddings()`
- **차원**: 4096
- **용도**:
  - 크롤링된 문서를 벡터로 변환
  - ChromaDB에 벡터 저장

#### 2.2 쿼리 임베딩
- **모델 옵션**:
  - `solar-embedding-1-large`: 일반용
  - `solar-embedding-1-large-query`: 쿼리 최적화
  - `solar-embedding-1-large-passage`: 문서 최적화
- **용도**: 사용자 질문을 벡터로 변환하여 유사도 검색

---

## RAG 시스템 처리 과정

### 전체 플로우

```
[사용자 질문]
     ↓
[1. 전처리]
     ↓
[2. 검색 (Retrieval)]
     ├─→ Vector Search (ChromaDB)
     └─→ SQL Search (SQLite)
     ↓
[3. 컨텍스트 생성]
     ↓
[4. 프롬프트 구성]
     ↓
[5. 생성 (Generation)]
     ↓
[6. 후처리]
     ↓
[최종 답변]
```

### 단계별 상세 설명

#### 1단계: 전처리
- **위치**: `demo_with_memory.py` (라인 249-255)
- **처리 내용**:
  - 사용자 입력 검증
  - 메시지 히스토리에 추가
  - UI에 사용자 메시지 표시

#### 2단계: 검색 (Retrieval)
- **위치**: `retriever.py` (라인 45-150)
- **처리 과정**:

##### 2.1 Vector Search
```python
# retriever.py - vector_search() 메서드
def vector_search(query: str, k: int = 5):
    # 1. 질문을 Solar Embedding으로 벡터화
    query_vector = embeddings.embed_query(query)

    # 2. ChromaDB에서 유사도 검색
    docs_with_scores = vector_db.search_with_scores(query, k=k)

    # 3. 점수 기반 필터링 및 정렬
    return filtered_results
```

##### 2.2 SQL Search
```python
# retriever.py - sql_search() 메서드
def sql_search(query: str, k: int = 5):
    # 키워드 기반 SQLite 검색
    sql_query = """
    SELECT doc_id, title, url, content,
    (CASE
        WHEN title LIKE ? THEN 3
        WHEN content LIKE ? THEN 1
        ELSE 0
    END) as relevance_score
    FROM documents
    WHERE title LIKE ? OR content LIKE ?
    ORDER BY relevance_score DESC
    LIMIT ?
    """
    return sql_results
```

##### 2.3 하이브리드 병합
```python
# retriever.py - search() 메서드
def search(query: str, k: int = 5, mode: str = "hybrid"):
    vector_results = vector_search(query, k)
    sql_results = sql_search(query, k)

    # 중복 제거 및 점수 기반 재정렬
    merged_results = merge_and_rank(vector_results, sql_results)
    return merged_results[:k]
```

#### 3단계: 컨텍스트 생성
- **위치**: `demo_with_memory.py` (라인 279-291)
- **처리 내용**:
  ```python
  # 검색된 문서들을 컨텍스트로 조합
  context = "\n\n".join([doc.page_content[:500] for doc in docs])

  # 소스 정보 수집
  sources = []
  for doc in docs[:3]:
      title = doc.metadata.get('title', 'Unknown')
      url = doc.metadata.get('url', '#')
      sources.append(f"[{title}]({url})")
  ```

#### 4단계: 프롬프트 구성
- **위치**: `demo_with_memory.py` - `generate_response_with_memory()` (라인 124-145)
- **프롬프트 템플릿**:
  ```python
  prompt = f"""당신은 LangChain 전문가 AI 어시스턴트입니다.
  아래 제공된 컨텍스트와 이전 대화 내용을 참고하여 사용자의 질문에 답변해주세요.

  {conversation_history}

  현재 컨텍스트:
  {context}

  현재 질문: {query}

  지침:
  1. 이전 대화 맥락을 고려하여 답변하세요
  2. 사용자가 "그것", "이것", "위의" 등 지시대명사를 사용하면 이전 대화에서 언급된 내용을 참고하세요
  3. 연속된 질문인 경우 이전 답변을 바탕으로 더 자세히 설명하세요
  4. 컨텍스트에 없는 내용은 추론하지 말고 모른다고 답하세요

  답변:"""
  ```

#### 5단계: 생성 (Generation)
- **위치**: `demo_with_memory.py` (라인 146-152)
- **Solar LLM 호출**:
  ```python
  # Solar LLM으로 답변 생성
  response = st.session_state.llm.invoke(prompt)

  # 대화 관리자에 기록
  if st.session_state.conversation_manager:
      conversation_manager.add_user_message(query)
      conversation_manager.add_assistant_message(response.content)
  ```

#### 6단계: 후처리
- **위치**: `demo_with_memory.py` (라인 314-323)
- **처리 내용**:
  - 응답 포맷팅
  - 소스 정보 추가
  - UI에 표시
  - 대화 히스토리 업데이트

---

## 상세 처리 플로우

### 예시: "LangChain에서 메모리를 사용하는 방법"

```python
# 1. 사용자 입력
user_query = "LangChain에서 메모리를 사용하는 방법"

# 2. 임베딩 생성 (Solar Embedding API 호출 #1)
query_embedding = solar_embedding.embed_query(user_query)
# → 4096차원 벡터 생성

# 3. Vector Search
vector_results = chromadb.similarity_search(
    query_embedding,
    k=5,
    filter={"category": "memory"}
)
# → 상위 5개 유사 문서 검색

# 4. SQL Search (Solar API 호출 없음)
sql_results = sqlite.execute(
    "SELECT * FROM documents WHERE content LIKE '%메모리%' LIMIT 5"
)

# 5. 결과 병합
all_docs = merge_results(vector_results, sql_results)
# → 최종 5개 문서 선택

# 6. 컨텍스트 생성
context = format_documents(all_docs)
# → "문서1 내용...\n\n문서2 내용..."

# 7. LLM 응답 생성 (Solar LLM API 호출 #2)
final_prompt = build_prompt(user_query, context, conversation_history)
response = solar_llm.invoke(final_prompt)
# → 최종 답변 생성

# 8. 결과 반환
return {
    "answer": response.content,
    "sources": [doc.metadata for doc in all_docs],
    "tokens_used": response.usage
}
```

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                 사용자 인터페이스                      │
│              (Streamlit - demo_with_memory.py)       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                  RAG 오케스트레이터                   │
│                 (main.py / main_simple.py)           │
└─────────┬───────────────────┬───────────────────────┘
          │                   │
          ▼                   ▼
┌──────────────────┐  ┌──────────────────────────────┐
│  검색 시스템       │  │      생성 시스템              │
│  (retriever.py)   │  │   (Solar LLM via llm.py)     │
└────┬──────┬──────┘  └──────────────────────────────┘
     │      │                        ▲
     ▼      ▼                        │
┌────────┐ ┌────────┐               │
│ChromaDB│ │SQLite  │               │
│        │ │   DB   │  ─────────────┘
│ Vector │ │Keyword │    Context
│ Store  │ │Search  │
└────────┘ └────────┘

Solar API 호출 지점:
① 문서 인덱싱 시: Solar Embedding
② 질문 벡터화 시: Solar Embedding
③ 답변 생성 시: Solar LLM
④ SQL 쿼리 생성 시: Solar LLM
```

---

## 코드 예시

### 1. Solar Embedding 사용
```python
# llm.py (라인 53-82)
def get_embeddings(model: str = "solar-embedding-1-large") -> Embeddings:
    api_key = os.getenv("UPSTAGE_API_KEY")
    return UpstageEmbeddings(
        api_key=api_key,
        model=model
    )

# vector_database.py에서 사용
embeddings = get_embeddings()
vectorstore = Chroma(
    collection_name="langchain_docs",
    embedding_function=embeddings,
    persist_directory="./data/chroma_db"
)
```

### 2. Solar LLM 사용
```python
# llm.py (라인 15-50)
def get_llm(model: str = "solar-pro", temperature: float = 0.1):
    return ChatUpstage(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2000
    )

# demo_with_memory.py에서 사용
llm = get_llm()
response = llm.invoke(prompt)
```

### 3. 하이브리드 검색
```python
# retriever.py (라인 151-195)
def search(self, query: str, k: int = 5, mode: str = "hybrid"):
    if mode == "hybrid":
        # Vector + SQL 병합
        vector_results = self.vector_search(query, k)
        sql_results = self.sql_search(query, k)

        # 점수 기반 재정렬
        all_results = vector_results + sql_results
        seen = set()
        unique_results = []

        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            doc_id = result.document.metadata.get("doc_id")
            if doc_id not in seen:
                seen.add(doc_id)
                unique_results.append(result)

        return [r.document for r in unique_results[:k]]
```

---

## API 호출 시점

### 초기화 단계 (1회성)
1. **문서 크롤링 후 인덱싱**
   - 63개 문서 × Solar Embedding = 63회 API 호출
   - 배치 처리로 최적화 (100개씩 묶어서 처리)

### 런타임 단계 (사용자 질문마다)
1. **사용자 질문 처리**
   - 질문 임베딩: 1회 Solar Embedding API 호출
   - 답변 생성: 1회 Solar LLM API 호출
   - **총 2회 API 호출 per 질문**

2. **SQL 쿼리 탭 사용 시**
   - 자연어→SQL 변환: 1회 Solar LLM API 호출

### API 호출 빈도 예상
- 일반 사용: 분당 2-10회 (사용자 질문 빈도에 따름)
- 초기 로딩: 63-100회 (문서 수에 따름)
- SQL 기능: 선택적 추가 호출

---

## 최적화 포인트

### 현재 구현의 장점
1. **하이브리드 검색**: Vector + Keyword로 정확도 향상
2. **대화 메모리**: 연속 질문 처리 가능
3. **배치 처리**: 임베딩 생성 시 효율화
4. **구조 기반 청킹**: 코드 블록 보존으로 품질 향상

### 개선 가능한 부분

#### 1. 캐싱 전략
```python
# 제안: 질문-답변 캐싱
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(query_hash: str):
    # 자주 묻는 질문은 캐시에서 반환
    return cached_response
```

#### 2. 임베딩 재사용
```python
# 제안: 임베딩 벡터 캐싱
embedding_cache = {}

def get_query_embedding(query: str):
    if query in embedding_cache:
        return embedding_cache[query]

    embedding = solar_embedding.embed_query(query)
    embedding_cache[query] = embedding
    return embedding
```

#### 3. 동적 컨텍스트 크기
```python
# 제안: 질문 복잡도에 따른 동적 k값
def get_dynamic_k(query: str) -> int:
    if is_complex_query(query):
        return 10  # 복잡한 질문은 더 많은 문서 참조
    return 5   # 단순 질문은 적은 문서로 충분
```

#### 4. 비동기 처리
```python
# 제안: Vector/SQL 검색 병렬 처리
import asyncio

async def parallel_search(query: str):
    vector_task = asyncio.create_task(vector_search_async(query))
    sql_task = asyncio.create_task(sql_search_async(query))

    vector_results, sql_results = await asyncio.gather(vector_task, sql_task)
    return merge_results(vector_results, sql_results)
```

#### 5. 토큰 사용량 최적화
```python
# 제안: 컨텍스트 압축
def compress_context(documents: List[Document], max_tokens: int = 1500):
    # 중요도 기반 문서 요약
    compressed = []
    token_count = 0

    for doc in sorted(documents, key=lambda x: x.score, reverse=True):
        doc_tokens = count_tokens(doc.content)
        if token_count + doc_tokens <= max_tokens:
            compressed.append(doc)
            token_count += doc_tokens
        else:
            # 문서 요약 후 추가
            summary = summarize(doc.content, max_tokens - token_count)
            compressed.append(summary)
            break

    return compressed
```

---

## 결론

현재 LangChain RAG 시스템은 Solar API를 효율적으로 활용하고 있습니다:

1. **최소 API 호출**: 질문당 2회 (임베딩 1회, LLM 1회)
2. **하이브리드 검색**: 정확도와 재현율 균형
3. **구조화된 처리**: 명확한 단계별 파이프라인

추가 최적화를 통해 API 비용을 더욱 절감하고 응답 속도를 개선할 수 있습니다.

---

*작성일: 2025-10-29*
*버전: 1.0*
*작성자: LangChain RAG 시스템 분석팀*