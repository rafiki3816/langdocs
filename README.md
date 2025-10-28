# 🤖 LangChain 문서 RAG 챗봇

LangChain 공식 문서를 기반으로 하는 지능형 RAG (Retrieval-Augmented Generation) 챗봇 시스템입니다.

## 📚 목차

- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치 가이드](#설치-가이드)
- [사용 방법](#사용-방법)
- [데이터베이스 스키마](#데이터베이스-스키마)
- [모듈 구조](#모듈-구조)
- [API 문서](#api-문서)
- [테스트](#테스트)
- [기여 가이드](#기여-가이드)
- [라이센스](#라이센스)

## 🚀 주요 기능

### 핵심 기능 (7개)
1. **System Prompt 엔지니어링** - LangChain 문서 전문 시스템 구축
2. **데이터 수집** - 웹 크롤링 및 문서 파싱
3. **VectorDB 통합** - ChromaDB를 통한 임베딩 저장
4. **RAG 검색/응답** - 하이브리드 검색 (벡터 + SQL)
5. **대화 메모리 관리** - 대화 컨텍스트 유지 및 메모리 저장
6. **Streamlit UI** - 웹 기반 사용자 인터페이스
7. **통합 main.py** - 전체 시스템 통합

### 추가 기능 (2개)
1. **성능 평가** - 답변 품질 및 속도 평가
2. **Text-to-SQL RAG** - 자연어를 SQL로 변환

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI (demo.py)                   │
│                 웹 인터페이스 및 시각화                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Main Integration (main.py)                    │
│                 모든 컴포넌트 통합 및 오케스트레이션         │
└────────────────────────┬────────────────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ LLM Manager │   │  Retriever  │   │Conversation │
│  (llm.py)   │   │(retriever.py)│  │   Manager   │
└─────────────┘   └─────────────┘   │(conversation│
                                     │    .py)     │
                                     └─────────────┘
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Vector DB  │   │Data Collector│  │Text-to-SQL │
│(vector_db.py│   │(data_collector│ │    RAG     │
└─────────────┘   │    .py)      │   │(text_to_sql│
                  └──────────────┘   │    .py)    │
                                     └─────────────┘
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Evaluator  │   │   Prompts   │   │   Config   │
│(evaluator.py│   │(prompts.py) │   │ Manager    │
└─────────────┘   └─────────────┘   │(config.py) │
                                     └─────────────┘
┌─────────────────────────────────────────────────────────────┐
│                         ▼                                    │
│              Databases & Storage                             │
│                        ▼                                     │
│     ┌──────────────────┴──────────────────┐                │
│     ▼                                      ▼                │
│  ChromaDB                              SQLite               │
│ (Vector Storage)                  (Metadata & Logs)         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📦 설치 가이드

### 시스템 요구사항
- Python 3.10 이상
- 4GB 이상의 RAM
- 10GB 이상의 디스크 공간

### 1. 저장소 복제
```bash
git clone https://github.com/your-username/langchain-rag-chatbot.git
cd langchain-rag-chatbot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 API 키 설정
```

필수 환경변수:
```
UPSTAGE_API_KEY=your_upstage_api_key_here
DATABASE_URL=sqlite:///./data/langchain.db
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
```

### 5. 초기 데이터베이스 설정
```bash
python scripts/init_db.py
```

## 🎮 사용 방법

### 웹 UI 실행 (Streamlit)
```bash
python main.py
# 또는
streamlit run demo.py
```

### CLI 모드
```bash
# 대화 모드
python main.py --mode chat

# 단일 질문
python main.py --mode chat --question "LangChain이 무엇인가요?"

# 데이터 수집
python main.py --mode collect --urls https://python.langchain.com/docs/get_started

# 시스템 평가
python main.py --mode evaluate

# SQL 쿼리
python main.py --mode chat --sql --question "최근 문서 5개를 보여주세요"
```

### Python API 사용
```python
from main import LangChainRAGChatbot

# 챗봇 초기화
chatbot = LangChainRAGChatbot()

# 대화 시작
conversation_id = chatbot.create_new_conversation()

# 질문하기
response = chatbot.chat(
    question="LangChain의 주요 컴포넌트는 무엇인가요?",
    conversation_id=conversation_id
)

print(response['answer'])
```

## 💾 데이터베이스 스키마

### SQLite 스키마

#### 1. documents 테이블
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT UNIQUE NOT NULL,      -- 문서 고유 ID
    title TEXT NOT NULL,               -- 문서 제목
    content TEXT NOT NULL,             -- 문서 내용
    url TEXT,                          -- 원본 URL
    category TEXT,                     -- 카테고리 (tutorials, how-to, reference 등)
    doc_type TEXT,                     -- 문서 유형 (guide, api, concept 등)
    chunk_index INTEGER,               -- 청크 인덱스
    total_chunks INTEGER,              -- 전체 청크 수
    metadata TEXT,                     -- JSON 형식 메타데이터
    embedding_id TEXT,                 -- 벡터 DB와 연결 ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_doc_type ON documents(doc_type);
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

#### 2. code_examples 테이블
```sql
CREATE TABLE code_examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,              -- documents 테이블 참조
    title TEXT,                        -- 코드 예제 제목
    code TEXT NOT NULL,                -- 코드 내용
    language TEXT DEFAULT 'python',    -- 프로그래밍 언어
    description TEXT,                  -- 설명
    output TEXT,                       -- 예상 출력
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
);

-- 인덱스
CREATE INDEX idx_code_examples_doc_id ON code_examples(doc_id);
CREATE INDEX idx_code_examples_language ON code_examples(language);
```

#### 3. api_references 테이블
```sql
CREATE TABLE api_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,              -- documents 테이블 참조
    class_name TEXT,                   -- 클래스 이름
    method_name TEXT,                  -- 메서드 이름
    parameters TEXT,                   -- 파라미터 정보 (JSON)
    returns TEXT,                      -- 반환 값
    description TEXT,                  -- 설명
    example_usage TEXT,                -- 사용 예제
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
);

-- 인덱스
CREATE INDEX idx_api_references_class ON api_references(class_name);
CREATE INDEX idx_api_references_method ON api_references(method_name);
```

#### 4. conversations 테이블
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,               -- 대화 세션 ID
    title TEXT,                        -- 대화 제목
    summary TEXT,                      -- 대화 요약
    metadata TEXT,                     -- JSON 형식 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. messages 테이블
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,     -- conversations 테이블 참조
    role TEXT NOT NULL,                -- 'user' 또는 'assistant'
    content TEXT NOT NULL,             -- 메시지 내용
    metadata TEXT,                     -- JSON 형식 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);

-- 인덱스
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

#### 6. evaluations 테이블
```sql
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,            -- 평가용 질문
    generated_answer TEXT,             -- 생성된 답변
    reference_answer TEXT,             -- 참조 답변
    relevance_score REAL,              -- 관련성 점수 (0-1)
    accuracy_score REAL,               -- 정확도 점수 (0-1)
    completeness_score REAL,           -- 완전성 점수 (0-1)
    response_time REAL,                -- 응답 시간 (초)
    retrieval_precision REAL,          -- 검색 정밀도
    retrieval_recall REAL,             -- 검색 재현율
    overall_score REAL,                -- 종합 점수 (0-1)
    metadata TEXT,                     -- JSON 형식 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_evaluations_overall_score ON evaluations(overall_score);
CREATE INDEX idx_evaluations_created_at ON evaluations(created_at);
```

### ChromaDB 컬렉션 구조

#### langchain_docs 컬렉션
```python
{
    "ids": ["doc_001_chunk_0", "doc_001_chunk_1", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    "metadatas": [
        {
            "doc_id": "doc_001",
            "title": "Introduction to LangChain",
            "url": "https://...",
            "category": "tutorials",
            "chunk_index": 0,
            "created_at": "2024-01-01T00:00:00"
        },
        ...
    ],
    "documents": ["LangChain is a framework...", "It provides...", ...]
}
```

## 📁 모듈 구조

### 핵심 모듈 (13개)

1. **llm.py** - LLM 및 임베딩 관리
   - Upstage Solar LLM 초기화
   - 임베딩 모델 관리
   - API 키 검증

2. **vector_database.py** - 벡터 데이터베이스 관리
   - ChromaDB 초기화 및 관리
   - 문서 추가/검색/삭제
   - 컬렉션 관리

3. **prompts.py** - 프롬프트 템플릿 관리
   - 시스템 프롬프트
   - Few-shot 예제
   - 컨텍스트 포맷팅

4. **data_collector.py** - 데이터 수집 및 처리
   - 웹 크롤링
   - 문서 파싱
   - 메타데이터 추출

5. **retriever.py** - 검색 시스템
   - 하이브리드 검색 (벡터 + SQL)
   - 검색 결과 재순위화
   - LangChain BaseRetriever 구현

6. **conversation.py** - 대화 관리
   - 멀티턴 대화 처리
   - 메모리 관리 (Buffer, Summary, Window)
   - 대화 히스토리

7. **text_to_sql.py** - Text-to-SQL RAG
   - 자연어를 SQL로 변환
   - 데이터베이스 스키마 인식
   - 쿼리 실행

8. **evaluator.py** - 성능 평가
   - 답변 품질 평가
   - 검색 성능 메트릭
   - 배치 평가 지원

9. **demo.py** - Streamlit UI
   - 웹 기반 UI 인터페이스
   - 실시간 채팅
   - 설정 관리

10. **main.py** - 통합 모듈
    - 전체 시스템 통합
    - CLI/Web 인터페이스
    - 컴포넌트 초기화

11. **utils.py** - 유틸리티 함수
    - 텍스트 처리
    - 파일 I/O
    - 시간 관리 도구

12. **config.py** - 설정 관리
    - 환경 변수 설정
    - 환경별 구성
    - 설정 검증

13. **requirements.txt** - 의존성 목록

## 📖 API 문서

### LangChainRAGChatbot 클래스

#### 초기화
```python
chatbot = LangChainRAGChatbot(config={
    'model_name': 'solar-1-mini-chat',
    'temperature': 0.7,
    'search_mode': 'hybrid',
    'top_k': 5
})
```

#### 주요 메서드

##### chat()
```python
response = chatbot.chat(
    question="질문 내용",
    conversation_id="conv_123",  # 선택사항
    use_sql=False,               # SQL 모드
    evaluate=False               # 평가 모드
)
# 반환: {'answer': str, 'sources': list, 'error': str}
```

##### collect_documents()
```python
results = chatbot.collect_documents(
    urls=["https://example.com/docs"]
)
# 반환: {'total_documents': int, 'successful_urls': list, 'failed_urls': list}
```

##### evaluate_system()
```python
stats = chatbot.evaluate_system(
    test_cases=[
        {'question': '...', 'reference_answer': '...'}
    ]
)
# 반환: {'avg_overall_score': float, 'avg_response_time': float, ...}
```

## 🧪 테스트

### 전체 테스트 실행
```bash
python -m pytest tests/ -v
```

### 개별 모듈 테스트
```bash
# LLM 모듈 테스트
python llm.py

# 벡터 DB 테스트
python vector_database.py

# Retriever 테스트
python retriever.py

# 평가 시스템 테스트
python evaluator.py
```

### 통합 테스트
```bash
python scripts/test_integration.py
```

## 🤝 기여 가이드

### 브랜치 전략
- `main`: 안정화된 버전
- `develop`: 개발 버전
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드 업무 수정
```

### Pull Request 체크리스트
- [ ] 코드가 스타일 가이드를 준수함
- [ ] 모든 테스트가 통과함
- [ ] 문서가 업데이트됨
- [ ] 성능 영향을 고려함
- [ ] 보안 이슈를 검토함

## 📊 성능 지표

### 권장 설정
1. **청크 크기**: 1000자 청크, 200자 중복
2. **검색 설정**: Top-5 문서, 하이브리드 검색
3. **캐싱**: 자주 사용되는 쿼리 캐싱
4. **배치 처리**: 임베딩 생성 시 100개 배치

### 벤치마크
- 응답 시간: 평균 2초 이내
- 검색 정확도: 80% 이상
- 메모리 사용량: 2GB 이하

## 🔒 보안 고려사항

1. **API 키 관리**
   - 환경 변수 사용
   - .env 파일을 .gitignore에 추가
   - 프로덕션에서 시크릿 매니저 사용

2. **데이터 보호**
   - SQLite 데이터베이스 암호화
   - HTTPS 통신 사용
   - 민감정보 마스킹

3. **접근 제어**
   - 인증/인가 구현
   - Rate limiting 적용
   - 입력 검증 강화

## 🔧 기능 개발 가이드

1. 이슈 생성 및 논의
2. 브랜치 생성 (`feature/issue-번호`)
3. 코드 작성 및 테스트
4. 테스트 코드 작성
5. Pull Request 생성
6. 코드 리뷰 및 수정
7. 병합

## 📄 라이센스

MIT License

Copyright (c) 2025 LangChain RAG Chatbot

## 📞 문의 및 지원

- 이슈 리포트: [GitHub Issues](https://github.com/your-username/langchain-rag-chatbot/issues)
- 이메일: support@example.com
- 문서: [https://docs.example.com](https://docs.example.com)

## 🙏 감사의 글

- LangChain 팀
- Upstage AI
- ChromaDB 팀
- 오픈소스 커뮤니티

---

**마지막 업데이트**: 2025-10-28
**버전**: 1.0.0
**상태**: Production Ready