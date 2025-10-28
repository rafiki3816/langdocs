# 🚧 개발 로드맵 - 남은 작업들

## 📊 현재 완성도: 75%

### ✅ 완료된 부분 (작동 중)
- ✅ LLM 연결 (Upstage Solar)
- ✅ 벡터 DB (ChromaDB)
- ✅ 데이터 수집 (Web Crawler)
- ✅ 기본 검색 (Retriever)
- ✅ SQLite 데이터베이스
- ✅ Streamlit UI (demo_simple.py)
- ✅ 간단한 메인 파일 (main_simple.py)

### ⚠️ 부분적으로 작동 (수정 필요)
- ⚠️ 원본 main.py (구문 오류)
- ⚠️ retriever.py (import 오류)
- ⚠️ conversation.py (import 오류)
- ⚠️ prompts.py (문자열 오류)
- ⚠️ evaluator.py (구문 오류)
- ⚠️ demo.py (원본 파일)

---

## 🔴 우선순위 높음 - 핵심 기능 개선

### 1. 📚 **더 많은 문서 수집** (현재 3개 → 50개+)
**필요한 이유**: 답변 품질 향상
```bash
# 추천 문서 리스트
- LangChain 핵심 개념 문서
- 모든 모듈 가이드 (model_io, chains, agents, memory)
- 튜토리얼 및 예제
- API 레퍼런스
```

**작업 방법**:
```python
# data_collector.py에 추가 URL 리스트 작성
urls = [
    # 50개 이상의 핵심 문서 URL
]
```

### 2. 🔧 **구문 오류 수정**
**영향받는 파일들**:
- `main.py` - 메인 통합 파일
- `retriever.py` - 하이브리드 검색
- `conversation.py` - 대화 관리
- `prompts.py` - 프롬프트 템플릿
- `evaluator.py` - 평가 시스템

**수정 방법**:
```python
# 공통 패턴 수정
- import 문 공백 누락: "fromtypingimport" → "from typing import"
- 클래스 정의: "cl as s" → "class"
- 화살표 함수: "-을" → "->"
- 조건문: "ifnot" → "if not"
```

### 3. 💬 **대화 메모리 구현**
**현재**: 세션 내에서만 대화 기록 유지
**목표**: 영구 저장 및 컨텍스트 관리

```python
# conversation.py 개선
class ConversationManager:
    def save_to_db(self, conversation_id, messages):
        # SQLite에 대화 저장

    def load_from_db(self, conversation_id):
        # 이전 대화 불러오기

    def summarize_context(self, messages):
        # 긴 대화 요약
```

---

## 🟡 우선순위 중간 - 기능 확장

### 4. 🔍 **검색 성능 개선**
```python
# retriever.py 개선 사항
- 재순위화 (Reranking) 알고리즘
- 하이브리드 가중치 조절
- 메타데이터 필터링 강화
- 의미적 유사도 + 키워드 매칭 최적화
```

### 5. 📊 **평가 시스템 완성**
```python
# evaluator.py 완성
- RAGAS 메트릭 구현
- 자동 평가 파이프라인
- 성능 대시보드
- A/B 테스트 기능
```

### 6. 🗄️ **Text-to-SQL 통합**
```python
# text_to_sql.py 활성화
- 자연어 → SQL 변환
- 데이터베이스 스키마 인식
- 쿼리 실행 및 결과 포맷팅
```

### 7. 🎨 **UI/UX 개선**
```python
# Streamlit 개선
- 다크 모드
- 파일 업로드 기능
- PDF 문서 직접 업로드
- 대화 내보내기 (PDF/Markdown)
- 음성 입력 지원
```

---

## 🟢 우선순위 낮음 - 고급 기능

### 8. 🤖 **멀티 LLM 지원**
```python
# 다양한 LLM 제공자 지원
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- Local LLMs (Ollama)
```

### 9. 🌐 **API 서버 구축**
```python
# FastAPI 서버
from fastapi import FastAPI

app = FastAPI()

@app.post("/chat")
async def chat(question: str):
    # REST API 엔드포인트

@app.websocket("/ws")
async def websocket_chat():
    # 실시간 웹소켓 채팅
```

### 10. 🔐 **인증 및 보안**
```python
# 사용자 관리
- 로그인/회원가입
- 세션 관리
- API 키 관리
- Rate limiting
```

### 11. 📈 **모니터링 및 로깅**
```python
# 프로덕션 준비
- Prometheus 메트릭
- ELK 스택 로깅
- 에러 추적 (Sentry)
- 성능 모니터링
```

### 12. 🐳 **컨테이너화**
```dockerfile
# Dockerfile
FROM python:3.10
# Docker 이미지 생성
# docker-compose.yml 작성
```

---

## 📅 개발 일정 제안

### Week 1 (이번 주)
- [ ] 50개 이상 문서 수집
- [ ] 구문 오류 완전 수정
- [ ] 대화 메모리 구현
- [ ] 검색 성능 테스트

### Week 2
- [ ] 평가 시스템 완성
- [ ] Text-to-SQL 통합
- [ ] UI 개선 (파일 업로드)
- [ ] 재순위화 구현

### Week 3
- [ ] FastAPI 서버 구축
- [ ] 멀티 LLM 지원
- [ ] 대화 내보내기 기능
- [ ] 성능 최적화

### Week 4
- [ ] Docker 컨테이너화
- [ ] 인증 시스템
- [ ] 프로덕션 배포
- [ ] 문서화 완성

---

## 🛠️ 즉시 수정 가능한 작업들

### 1. Import 오류 일괄 수정
```bash
# 모든 파일의 import 오류 수정
find . -name "*.py" -exec sed -i '' 's/fromtypingimport/from typing import/g' {} \;
find . -name "*.py" -exec sed -i '' 's/importList/import List/g' {} \;
```

### 2. 추가 문서 URL 리스트
```python
additional_urls = [
    "https://python.langchain.com/docs/modules/model_io/chat",
    "https://python.langchain.com/docs/modules/model_io/output_parsers",
    "https://python.langchain.com/docs/modules/data_connection",
    "https://python.langchain.com/docs/modules/chains/foundational",
    "https://python.langchain.com/docs/modules/chains/popular",
    "https://python.langchain.com/docs/modules/agents/agent_types",
    "https://python.langchain.com/docs/modules/agents/tools",
    "https://python.langchain.com/docs/modules/memory/types",
    "https://python.langchain.com/docs/expression_language/interface",
    "https://python.langchain.com/docs/expression_language/primitives",
    # ... 더 많은 URL
]
```

### 3. 성능 측정 스크립트
```python
# benchmark.py
import time
from main_simple import LangChainRAGChatbot

def benchmark():
    chatbot = LangChainRAGChatbot()

    test_questions = [
        "LangChain이란?",
        "체인과 에이전트의 차이는?",
        "벡터 데이터베이스 사용법은?",
    ]

    for q in test_questions:
        start = time.time()
        response = chatbot.chat(q)
        elapsed = time.time() - start
        print(f"질문: {q}")
        print(f"시간: {elapsed:.2f}초")
        print("---")
```

---

## 💡 추천 개발 순서

### 🥇 **1단계: 데이터 확충** (오늘)
- 50개 문서 수집
- 카테고리별 균형 맞추기
- 수집 후 테스트

### 🥈 **2단계: 코드 정리** (내일)
- 모든 구문 오류 수정
- import 문제 해결
- 테스트 코드 작성

### 🥉 **3단계: 기능 개선** (이번 주)
- 대화 메모리 구현
- 검색 성능 개선
- 평가 시스템 활성화

### 🏆 **4단계: 프로덕션** (다음 주)
- API 서버 구축
- Docker 이미지
- 배포 준비

---

## 📌 핵심 포인트

**현재 작동하는 것**: 기본 RAG 챗봇 기능 (75%)
**가장 중요한 개선**: 문서 수 확충 (3개 → 50개+)
**가장 쉬운 개선**: import 오류 수정
**가장 큰 영향**: 대화 메모리 구현

---

**결론**: 기본 기능은 작동하지만, 프로덕션 레벨까지는 2-4주 추가 개발이 필요합니다.