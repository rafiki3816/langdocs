# 🚀 LangChain RAG 챗봇 실행 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [로컬 환경 실행](#로컬-환경-실행)
3. [Docker 환경 실행](#docker-환경-실행)
4. [주요 기능](#주요-기능)
5. [문제 해결](#문제-해결)

---

## 사전 준비

### 1. 환경 설정 확인
```bash
# 프로젝트 디렉토리로 이동
cd /Users/dongjunekim/ai/langChainDocs

# Python 가상환경 확인
source venv/bin/activate

# 의존성 설치 확인
pip list | grep -E "langchain|streamlit|chromadb|upstage"
```

### 2. API 키 설정
`.env` 파일에 Upstage API 키가 설정되어 있는지 확인:
```bash
cat .env | grep UPSTAGE_API_KEY
```

만약 없다면:
```bash
echo "UPSTAGE_API_KEY=your-api-key-here" >> .env
```

### 3. 데이터 확인
```bash
# 크롤링된 문서 확인 (63개여야 함)
sqlite3 ./data/langchain.db "SELECT COUNT(*) FROM documents;"

# Vector DB 확인
ls -lah ./data/chroma_db/
```

---

## 로컬 환경 실행

### 방법 1: Streamlit UI (추천)

#### 메모리 기능 포함 버전 (추천)
```bash
# 터미널에서 실행
source venv/bin/activate
streamlit run demo_with_memory.py
```

실행 후 자동으로 브라우저가 열립니다. 또는 수동으로 접속:
- **URL**: http://localhost:8501

**주요 기능**:
- 💬 채팅: LangChain 문서 기반 질문/답변
- 📚 예제 질문: 연속 질문 예제
- ❓ 사용법: 시스템 사용 가이드
- 🔍 SQL 쿼리: 자연어→SQL, 직접 SQL 입력

#### 간단한 버전
```bash
streamlit run demo_simple.py
```

### 방법 2: Python 스크립트

#### 대화형 CLI
```bash
python main_simple.py
```

터미널에서 직접 질문하고 답변 받기:
```
질문을 입력하세요 (종료: exit): LangChain이란?
답변: ...
```

#### Vector DB 초기화
```bash
# 테스트 모드 (5개 문서)
python initialize_vector_db.py --test-only

# 전체 문서 로딩 (30개)
python initialize_vector_db.py --max-pages 30

# DB 초기화 후 로딩
python initialize_vector_db.py --reset --max-pages 30
```

---

## Docker 환경 실행

### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

### 2. Docker 실행 스크립트 사용

#### 서비스 시작
```bash
./docker_run.sh start
```

실행 후 접속:
- **ChromaDB**: http://localhost:8000
- **Streamlit**: http://localhost:8501

#### Vector DB 초기화
```bash
./docker_run.sh init-db
```

#### 서비스 상태 확인
```bash
./docker_run.sh status
```

#### 로그 확인
```bash
# 전체 로그
./docker_run.sh logs

# 특정 서비스 로그
./docker_run.sh logs chromadb
./docker_run.sh logs langchain-app
```

#### 서비스 중지
```bash
./docker_run.sh stop
```

#### 전체 정리 (데이터 삭제 포함)
```bash
./docker_run.sh clean
```

### 3. Docker Compose 직접 사용
```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 로그
docker-compose logs -f

# 재시작
docker-compose restart
```

---

## 주요 기능

### 1. 채팅 기능
- **일반 질문**: "LangChain이란 무엇인가요?"
- **연속 질문**: "그것의 주요 구성 요소는?"
- **코드 질문**: "메모리 사용 예제 코드 보여줘"

### 2. SQL 쿼리 탭

#### 자연어→SQL
```
질문: "모든 문서의 제목을 보여주세요"
→ SQL 자동 생성 및 실행
```

#### 직접 SQL
```sql
SELECT category, COUNT(*) as count
FROM documents
GROUP BY category
ORDER BY count DESC;
```

### 3. 대화 메모리
- 최근 10개 대화 기억
- 지시대명사 이해 ("그것", "이것")
- 컨텍스트 유지

---

## 실행 예시

### 시나리오 1: 처음 사용자
```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 시스템 테스트
python initialize_vector_db.py --test-only

# 3. Streamlit 실행
streamlit run demo_with_memory.py
```

브라우저에서:
1. 사이드바에서 "시스템 초기화" 클릭
2. "채팅" 탭에서 질문 입력
3. 결과 확인

### 시나리오 2: SQL 쿼리 사용
```bash
streamlit run demo_with_memory.py
```

브라우저에서:
1. "SQL 쿼리" 탭 선택
2. "자연어→SQL" 모드 선택
3. 예제 질문 선택하거나 직접 입력
4. "SQL로 변환 및 실행" 클릭

### 시나리오 3: Docker 환경
```bash
# 1. Docker 서비스 시작
./docker_run.sh start

# 2. Vector DB 초기화
./docker_run.sh init-db

# 3. 브라우저에서 접속
# http://localhost:8501
```

---

## 문제 해결

### Q1: "UPSTAGE_API_KEY가 설정되지 않았습니다" 오류
**해결방법**:
```bash
# .env 파일 확인
cat .env

# API 키 설정
echo "UPSTAGE_API_KEY=your-actual-api-key" >> .env

# 재실행
```

### Q2: 포트가 이미 사용 중
**해결방법**:
```bash
# 포트 사용 확인
lsof -i :8501

# 프로세스 종료
pkill -f streamlit

# 다른 포트로 실행
streamlit run demo_with_memory.py --server.port 8502
```

### Q3: "벡터 저장소 초기화 실패"
**해결방법**:
```bash
# ChromaDB 디렉토리 확인
ls -la ./data/chroma_db/

# 재초기화
python initialize_vector_db.py --reset --test-only
```

### Q4: Docker 연결 실패
**해결방법**:
```bash
# Docker 상태 확인
docker ps

# ChromaDB 헬스체크
curl http://localhost:8000/api/v1/heartbeat

# 재시작
./docker_run.sh restart
```

### Q5: 문서 검색이 안됨
**해결방법**:
```bash
# 문서 수 확인
sqlite3 ./data/langchain.db "SELECT COUNT(*) FROM documents;"

# Vector DB 재구축
python initialize_vector_db.py --reset --max-pages 30
```

### Q6: 느린 응답 속도
**해결 방법**:
- 검색 문서 수 줄이기 (사이드바에서 3개로 설정)
- 메모리 윈도우 줄이기 (5개로 설정)
- 네트워크 연결 확인 (Solar API 호출)

---

## 성능 모니터링

### Streamlit 통계 확인
사이드바의 "📊 통계" 섹션에서:
- 총 문서 수
- 대화 턴 수
- 평균 응답 길이

### Vector DB 상태
```bash
# 로컬 환경
python -c "from vector_database import VectorDatabase; vdb = VectorDatabase(); vdb.init_vectorstore(); print(vdb.get_statistics())"

# Docker 환경
curl http://localhost:8000/api/v1/collections
```

---

## 추가 리소스

### 문서
- **README.md**: 전체 프로젝트 개요
- **SOLAR_API_RAG_ANALYSIS.md**: Solar API 사용 분석

### GitHub
- **Repository**: https://github.com/rafiki3816/langdocs.git

### 참고 파일
- `llm.py`: Solar API 설정
- `retriever.py`: 검색 시스템
- `conversation.py`: 대화 메모리
- `text_to_sql.py`: SQL 생성

---

## 빠른 시작 명령어 요약

```bash
# 로컬 실행 (가장 간단)
source venv/bin/activate
streamlit run demo_with_memory.py

# Vector DB 테스트
python initialize_vector_db.py --test-only

# Docker 실행
./docker_run.sh start
./docker_run.sh init-db

# 포트 변경
streamlit run demo_with_memory.py --server.port 8502
```

---

*작성일: 2025-10-29*
*버전: 1.0*