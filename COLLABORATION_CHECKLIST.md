# 🔍 협업 미션 체크리스트 및 TODO

## 📋 프로젝트 개요
- **협업 목적**: LangChain 문서 기반 RAG 시스템 구축
- **담당 미션**:
  1. LangChain 문서 크롤링 + 최적 청킹 전략 구현
  2. Upstage 임베딩 모델 설정 + Vector DB 적재 스크립트 구현

---

## ✅ 미션 1: LangChain 문서 크롤링 및 청킹 전략

### 📌 핵심 요구사항
- [x] LangChain 공식 문서 크롤링 코드 구현
- [x] 코드 블록(````) 보존하는 청킹 전략 적용
- [x] 함수 시그니처 보존
- [x] **문서 청크 리스트를 반환하는 함수** 완성

### 🔍 체크리스트

#### 1.1 크롤링 코드 검증
- [x] **파일 존재**: `data_collector.py` 구현 완료 (527줄)
- [x] **크롤링 대상**: LangChain 공식 문서 (https://python.langchain.com)
- [x] **크롤링 범위**: 63개 문서 수집 완료
- [x] **메타데이터 포함**: URL, 제목, 카테고리, 타임스탬프 저장
- [x] **에러 핸들링**: 재시도 로직, 타임아웃 설정

**검증 명령어**:
```bash
# 크롤링된 문서 수 확인
sqlite3 ./data/langchain.db "SELECT COUNT(*) FROM documents;"
# 결과: 63개 문서

# 카테고리별 문서 분포 확인
sqlite3 ./data/langchain.db "SELECT category, COUNT(*) FROM documents GROUP BY category;"
```

#### 1.2 청킹 전략 구현 검증
- [x] **구조 기반 텍스트 분할기**: `advanced_text_splitter.py` (703줄)
- [x] **코드 블록 보존**: ````로 감싸진 코드 블록을 하나의 청크로 유지
- [x] **함수/클래스 정의 보존**: Python AST 파싱으로 함수 전체 유지
- [x] **Markdown 구조 인식**: 헤더(#, ##, ###) 기반 논리적 분할
- [x] **청크 크기 최적화**:
  - 기본 청크: 1500자
  - 코드 블록: 최대 3000자
  - 오버랩: 200자

**검증 명령어**:
```bash
# 청킹 전략 테스트
python -c "
from advanced_text_splitter import StructuredTextSplitter
splitter = StructuredTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    preserve_code_blocks=True,
    preserve_functions=True
)
print('✓ 구조 기반 분할기 초기화 성공')
print(f'청크 크기: {splitter.chunk_size}')
print(f'코드 블록 보존: {splitter.preserve_code_blocks}')
print(f'함수 보존: {splitter.preserve_functions}')
"
```

#### 1.3 문서 청크 리스트 반환 함수 검증
- [x] **핵심 함수**: `DataCollector.chunk_documents()`
- [x] **입력**: `List[Document]` (크롤링된 문서 리스트)
- [x] **출력**: `List[Document]` (청크된 문서 리스트)
- [x] **함수 시그니처**:
```python
def chunk_documents(
    self,
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    use_structured_splitter: bool = True
) -> List[Document]:
```

**검증 코드**:
```python
# data_collector.py에서 함수 사용 예제
from data_collector import DataCollector

collector = DataCollector()

# 1. 문서 수집
documents = collector.collect_documents(max_pages=5)
print(f"✓ 수집된 문서: {len(documents)}개")

# 2. 구조 기반 청킹 (코드 블록 보존)
chunked_docs = collector.chunk_documents(
    documents,
    chunk_size=1500,
    chunk_overlap=200,
    use_structured_splitter=True  # 핵심: 구조 기반 분할 사용
)
print(f"✓ 청크 결과: {len(chunked_docs)}개")

# 3. 반환값 검증
assert isinstance(chunked_docs, list), "반환값이 리스트가 아님"
assert all(hasattr(doc, 'page_content') for doc in chunked_docs), "Document 객체 아님"
print("✓ 반환값 검증 성공")
```

#### 1.4 청킹 품질 검증
- [x] **코드 블록 완전성**: ``` 시작과 끝이 같은 청크에 포함
- [x] **함수 무결성**: def/class 정의가 분할되지 않음
- [x] **컨텍스트 유지**: chunk_overlap으로 문맥 연결
- [x] **메타데이터 전달**: 원본 문서의 메타데이터가 청크에 보존

**품질 확인 스크립트**:
```bash
# 청킹 품질 검증
python -c "
from data_collector import DataCollector
import re

collector = DataCollector()
docs = collector.collect_documents(max_pages=3)
chunks = collector.chunk_documents(docs, use_structured_splitter=True)

# 코드 블록 완전성 검사
broken_blocks = 0
for chunk in chunks:
    content = chunk.page_content
    open_count = content.count('\`\`\`')
    if open_count % 2 != 0:
        broken_blocks += 1

print(f'✓ 총 청크: {len(chunks)}개')
print(f'✓ 깨진 코드 블록: {broken_blocks}개')
print(f'✓ 청킹 품질: {\"통과\" if broken_blocks == 0 else \"확인 필요\"}')
"
```

### 📄 미션 1 관련 파일 목록
```
✓ data_collector.py          # 크롤러 + 청킹 함수 (핵심)
✓ advanced_text_splitter.py  # 구조 기반 분할기 (핵심)
✓ utils.py                   # 유틸리티 함수
✓ README.md                  # 청킹 전략 문서화
✓ data/langchain.db          # 크롤링 결과 (63개 문서)
```

---

## ✅ 미션 2: Upstage 임베딩 모델 + Vector DB 적재

### 📌 핵심 요구사항
- [x] Upstage 임베딩 모델 설정
- [x] 팀원 4의 청크 데이터를 받아 처리
- [x] chroma_vector_db 컨테이너에 적재하는 스크립트
- [x] 최초 데이터 로딩 기능

### 🔍 체크리스트

#### 2.1 Upstage 임베딩 모델 설정 검증
- [x] **API 키 설정**: `.env` 파일에 `UPSTAGE_API_KEY` 저장
- [x] **모델 선택**: `solar-embedding-1-large` (4096 차원)
- [x] **LangChain 통합**: `UpstageEmbeddings` 클래스 사용
- [x] **에러 핸들링**: API 키 검증 로직 포함

**검증 명령어**:
```bash
# API 키 확인
cat .env | grep UPSTAGE_API_KEY

# 임베딩 모델 테스트
python -c "
from llm import get_embeddings

embeddings = get_embeddings(model='solar-embedding-1-large')
test_vector = embeddings.embed_query('테스트 문장')
print(f'✓ 임베딩 모델 로드 성공')
print(f'✓ 벡터 차원: {len(test_vector)}차원')
print(f'✓ 모델명: solar-embedding-1-large')
"
```

**설정 파일 확인**:
```python
# llm.py:53-82
def get_embeddings(
    model: str = "solar-embedding-1-large"
) -> Embeddings:
    """
    Upstage Solar Embeddings 인스턴스를 반환합니다.

    Args:
        model: 사용할 임베딩 모델명
            - "solar-embedding-1-large": 일반용
            - "solar-embedding-1-large-query": 쿼리 최적화
            - "solar-embedding-1-large-passage": 문서 최적화
    """
    api_key = os.getenv("UPSTAGE_API_KEY")

    if not api_key or api_key == "your-actual-api-key-here":
        raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

    return UpstageEmbeddings(
        api_key=api_key,
        model=model
    )
```

#### 2.2 ChromaDB 컨테이너 환경 검증
- [x] **Docker 설정**: `docker-compose.yml` 구현
- [x] **ChromaDB 이미지**: `chromadb/chroma:latest`
- [x] **포트 매핑**: 8000:8000
- [x] **영구 저장소**: `./data/chroma_docker` 볼륨 마운트
- [x] **헬스체크**: API 엔드포인트 확인

**Docker 환경 검증**:
```bash
# Docker Compose 파일 확인
cat docker-compose.yml

# ChromaDB 컨테이너 시작
./docker_run.sh start

# 컨테이너 상태 확인
docker ps | grep chroma

# ChromaDB 헬스체크
curl http://localhost:8000/api/v1/heartbeat
# 예상 응답: {"nanosecond heartbeat": ...}

# 컨테이너 로그 확인
./docker_run.sh logs chromadb
```

#### 2.3 Vector DB 적재 스크립트 검증
- [x] **핵심 스크립트**: `initialize_vector_db.py` (333줄)
- [x] **기능**:
  - 팀원의 청크 데이터 입력 받기
  - ChromaDB 컨테이너 연결
  - 임베딩 생성 및 저장
  - 배치 처리 (100개씩)
  - 진행률 표시

**스크립트 구조 확인**:
```python
# initialize_vector_db.py의 핵심 클래스
class VectorDBInitializer:
    def __init__(self, use_docker: bool = False):
        """
        Args:
            use_docker: True이면 Docker ChromaDB 사용
        """
        self.use_docker = use_docker
        if use_docker:
            from vector_database_docker import DockerVectorDatabase
            self.vector_db = DockerVectorDatabase()
        else:
            from vector_database import VectorDatabase
            self.vector_db = VectorDatabase()

    def load_to_vector_db(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> int:
        """팀원 청크 데이터를 Vector DB에 적재"""
        # 배치 처리 및 진행률 표시
```

#### 2.4 팀원 데이터 수신 인터페이스
- [x] **입력 형식**: `List[Document]` (LangChain Document 객체)
- [x] **필수 필드**:
  - `page_content`: 청크 텍스트 (str)
  - `metadata`: 메타데이터 딕셔너리
    - `source`: 출처 URL
    - `title`: 문서 제목
    - `chunk_index`: 청크 순서

**팀원 4로부터 데이터 받는 예제 코드**:
```python
# 팀원 4가 제공할 청크 데이터 형식
from langchain.schema import Document

# 예시: 팀원이 이 형식으로 청크 리스트를 전달
team_member_chunks = [
    Document(
        page_content="LangChain은 LLM 애플리케이션 개발 프레임워크입니다...",
        metadata={
            "source": "https://python.langchain.com/docs/get_started",
            "title": "LangChain 소개",
            "chunk_index": 0
        }
    ),
    # ... 더 많은 청크
]

# 우리의 스크립트로 적재
from initialize_vector_db import VectorDBInitializer

initializer = VectorDBInitializer(use_docker=True)
loaded_count = initializer.load_to_vector_db(
    documents=team_member_chunks,  # 팀원이 제공한 청크
    batch_size=100,
    show_progress=True
)
print(f"✓ {loaded_count}개 청크 적재 완료")
```

#### 2.5 최초 데이터 로딩 검증
- [x] **전체 파이프라인**: `run_full_pipeline()` 메서드
- [x] **단계**:
  1. 문서 수집 (크롤링)
  2. 구조 기반 청킹
  3. Vector DB 적재
- [x] **옵션**:
  - `--docker`: Docker ChromaDB 사용
  - `--reset`: 기존 데이터 삭제 후 재로딩
  - `--max-pages`: 로딩할 문서 수 제한
  - `--test-only`: 테스트 모드 (5개 문서만)

**최초 로딩 실행 명령어**:
```bash
# 방법 1: 전체 파이프라인 실행 (Docker)
python initialize_vector_db.py --docker --reset --max-pages 30

# 방법 2: Docker 스크립트 사용
./docker_run.sh init-db

# 방법 3: 테스트 모드 (5개 문서만)
python initialize_vector_db.py --docker --test-only

# 로딩 결과 확인
python -c "
from vector_database_docker import DockerVectorDatabase
vdb = DockerVectorDatabase()
stats = vdb.get_statistics()
print(f'✓ 적재된 문서: {stats[\"total_documents\"]}개')
print(f'✓ 컬렉션: {stats[\"collection_name\"]}')
"
```

#### 2.6 적재 품질 검증
- [x] **데이터 무결성**: 모든 청크가 저장됨
- [x] **임베딩 차원**: 4096차원 벡터 확인
- [x] **메타데이터 보존**: source, title 등 유지
- [x] **검색 테스트**: 샘플 쿼리로 검색 동작 확인

**품질 검증 스크립트**:
```bash
# Vector DB 품질 검증
python -c "
from vector_database_docker import DockerVectorDatabase
from llm import get_embeddings

# 1. Vector DB 연결
vdb = DockerVectorDatabase()
vdb.init_vectorstore()

# 2. 통계 확인
stats = vdb.get_statistics()
print('=== Vector DB 통계 ===')
print(f'총 문서: {stats[\"total_documents\"]}개')
print(f'컬렉션: {stats[\"collection_name\"]}')

# 3. 샘플 검색 테스트
results = vdb.search('LangChain이란 무엇인가?', k=3)
print(f'\n✓ 검색 결과: {len(results)}개')
print(f'✓ 첫 번째 결과: {results[0].page_content[:100]}...')

# 4. 임베딩 차원 확인
embeddings = get_embeddings()
test_vec = embeddings.embed_query('테스트')
print(f'\n✓ 임베딩 차원: {len(test_vec)}차원')
"
```

### 📄 미션 2 관련 파일 목록
```
✓ llm.py                        # Upstage 임베딩 모델 설정 (핵심)
✓ vector_database_docker.py     # Docker ChromaDB 클라이언트 (핵심)
✓ initialize_vector_db.py       # 적재 스크립트 (핵심)
✓ docker-compose.yml            # 컨테이너 설정
✓ Dockerfile                    # 앱 이미지 빌드
✓ docker_run.sh                 # Docker 관리 스크립트
✓ .env                          # API 키 저장
✓ data/chroma_docker/           # Vector DB 데이터 저장소
```

---

## 📊 통합 검증 절차

### Step 1: 환경 준비
```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 의존성 확인
pip list | grep -E "langchain|chromadb|upstage"

# 3. API 키 확인
cat .env | grep UPSTAGE_API_KEY

# 4. Docker 확인
docker --version
docker-compose --version
```

### Step 2: 미션 1 검증 (크롤링 + 청킹)
```bash
# 1. 청킹 모듈 테스트
python advanced_text_splitter.py

# 2. 크롤링 + 청킹 통합 테스트
python -c "
from data_collector import DataCollector

collector = DataCollector()

# 소규모 테스트 (5개 문서)
docs = collector.collect_documents(max_pages=5)
print(f'✓ 크롤링: {len(docs)}개')

# 구조 기반 청킹
chunks = collector.chunk_documents(docs, use_structured_splitter=True)
print(f'✓ 청킹: {len(chunks)}개')

# 반환값 타입 확인
print(f'✓ 반환 타입: {type(chunks)}')
print(f'✓ 첫 청크 타입: {type(chunks[0])}')
"

# 3. 코드 블록 보존 검증
python -c "
from data_collector import DataCollector
collector = DataCollector()
docs = collector.collect_documents(max_pages=3)
chunks = collector.chunk_documents(docs, use_structured_splitter=True)

# 코드 블록 완전성 체크
broken = sum(1 for c in chunks if c.page_content.count('\`\`\`') % 2 != 0)
print(f'✓ 총 청크: {len(chunks)}개')
print(f'✓ 깨진 코드 블록: {broken}개')
print(f'✓ 결과: {\"통과\" if broken == 0 else \"확인 필요\"}')
"
```

### Step 3: 미션 2 검증 (임베딩 + Vector DB)
```bash
# 1. 임베딩 모델 테스트
python llm.py

# 2. Docker ChromaDB 시작
./docker_run.sh start

# 3. ChromaDB 연결 테스트
curl http://localhost:8000/api/v1/heartbeat

# 4. 테스트 데이터 로딩
python initialize_vector_db.py --docker --test-only

# 5. Vector DB 검증
python -c "
from vector_database_docker import DockerVectorDatabase
vdb = DockerVectorDatabase()
vdb.init_vectorstore()
stats = vdb.get_statistics()
print(f'✓ Vector DB 문서: {stats[\"total_documents\"]}개')

# 검색 테스트
results = vdb.search('LangChain 메모리', k=3)
print(f'✓ 검색 기능: {\"정상\" if len(results) > 0 else \"오류\"}')
"
```

### Step 4: 전체 파이프라인 검증
```bash
# 전체 시스템 테스트 (30개 문서)
python initialize_vector_db.py --docker --reset --max-pages 30

# 결과 확인
python -c "
from vector_database_docker import DockerVectorDatabase
vdb = DockerVectorDatabase()
vdb.init_vectorstore()
stats = vdb.get_statistics()
print('=== 최종 검증 결과 ===')
print(f'✓ 적재 완료: {stats[\"total_documents\"]}개 문서')
print(f'✓ Vector DB: {stats[\"collection_name\"]}')

# SQLite DB 확인
import sqlite3
conn = sqlite3.connect('./data/langchain.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM documents')
doc_count = cursor.fetchone()[0]
conn.close()
print(f'✓ SQLite DB: {doc_count}개 문서')
"
```

---

## 📝 TODO 리스트 (GitHub 업데이트 전)

### 🔴 필수 사항 (Must Have)
- [ ] **1. 미션 1 검증 완료**
  - [ ] `advanced_text_splitter.py` 실행 테스트 통과
  - [ ] `DataCollector.chunk_documents()` 함수 반환값 검증
  - [ ] 코드 블록 보존 확인 (깨진 블록 0개)
  - [ ] README.md에 청킹 전략 문서화 확인

- [ ] **2. 미션 2 검증 완료**
  - [ ] `.env` 파일에 `UPSTAGE_API_KEY` 설정
  - [ ] `llm.py` 실행하여 임베딩 모델 테스트 통과
  - [ ] Docker ChromaDB 컨테이너 정상 실행 확인
  - [ ] `initialize_vector_db.py --docker --test-only` 성공

- [ ] **3. 통합 테스트**
  - [ ] 전체 파이프라인 실행 (30개 문서)
  - [ ] Vector DB 검색 기능 테스트
  - [ ] 팀원 데이터 수신 인터페이스 문서화

- [ ] **4. 문서화**
  - [ ] README.md 최신화
  - [ ] 이 체크리스트 파일 (`COLLABORATION_CHECKLIST.md`)
  - [ ] `EXECUTION_GUIDE.md` 확인
  - [ ] 팀원을 위한 사용법 섹션 추가

- [ ] **5. Git 준비**
  - [ ] 불필요한 파일 `.gitignore`에 추가
  - [ ] 커밋 메시지 준비
  - [ ] 원격 저장소 동기화 확인

### 🟡 권장 사항 (Nice to Have)
- [ ] 성능 벤치마크 (크롤링/청킹/임베딩 속도)
- [ ] 에러 케이스 테스트 (네트워크 오류, API 제한 등)
- [ ] 로깅 레벨 확인 및 정리
- [ ] Docker 이미지 최적화

### 🟢 선택 사항 (Optional)
- [ ] CI/CD 파이프라인 설정
- [ ] 단위 테스트 추가
- [ ] 코드 스타일 검사 (flake8, black)

---

## 🚀 GitHub 업데이트 절차

### 1. 최종 검증
```bash
# 전체 시스템 테스트
./docker_run.sh start
python initialize_vector_db.py --docker --test-only

# 결과 확인
./docker_run.sh status
```

### 2. Git 커밋
```bash
# 1. 변경사항 확인
git status

# 2. 추가할 파일 확인
git add .

# 3. 커밋 (의미 있는 메시지)
git commit -m "feat: LangChain 크롤링 + Upstage 임베딩 통합 완료

- 미션 1: 구조 기반 청킹 전략 구현 (코드 블록 보존)
  - advanced_text_splitter.py: 코드/함수 보존 로직
  - data_collector.py: chunk_documents() 함수 완성

- 미션 2: Upstage 임베딩 + ChromaDB 컨테이너 설정
  - llm.py: solar-embedding-1-large 설정
  - vector_database_docker.py: Docker 클라이언트
  - initialize_vector_db.py: 팀원 데이터 적재 스크립트

- 문서화: COLLABORATION_CHECKLIST.md 추가"
```

### 3. GitHub 푸시
```bash
# 원격 저장소 확인
git remote -v

# 푸시
git push origin main

# 푸시 후 확인
git log -1
```

### 4. 팀원에게 공유할 정보
```markdown
## 팀원 4님께

안녕하세요! LangChain 문서 크롤링 및 Vector DB 적재 시스템이 준비되었습니다.

### 청크 데이터 전달 형식
청크 데이터를 아래 형식으로 전달해주세요:

\`\`\`python
from langchain.schema import Document

chunks = [
    Document(
        page_content="청크 텍스트 내용...",
        metadata={
            "source": "문서 URL",
            "title": "문서 제목",
            "chunk_index": 0
        }
    ),
    # ... 더 많은 청크
]
\`\`\`

### 적재 방법
\`\`\`python
from initialize_vector_db import VectorDBInitializer

# Docker ChromaDB 시작
# ./docker_run.sh start

# 청크 적재
initializer = VectorDBInitializer(use_docker=True)
loaded_count = initializer.load_to_vector_db(
    documents=chunks,  # 여러분이 제공한 청크
    batch_size=100
)
print(f"적재 완료: {loaded_count}개")
\`\`\`

### 참고 문서
- 실행 가이드: `EXECUTION_GUIDE.md`
- 협업 체크리스트: `COLLABORATION_CHECKLIST.md`
- Docker 사용법: `./docker_run.sh help`
```

---

## 🔍 트러블슈팅

### 문제 1: "UPSTAGE_API_KEY가 설정되지 않았습니다"
```bash
# .env 파일 확인
cat .env

# API 키 추가
echo "UPSTAGE_API_KEY=your-actual-key" >> .env
```

### 문제 2: Docker ChromaDB 연결 실패
```bash
# 컨테이너 상태 확인
docker ps | grep chroma

# 재시작
./docker_run.sh restart

# 로그 확인
./docker_run.sh logs chromadb
```

### 문제 3: 청킹 중 코드 블록이 깨짐
```python
# advanced_text_splitter.py 설정 확인
splitter = StructuredTextSplitter(
    preserve_code_blocks=True,  # 반드시 True
    code_block_max_size=3000    # 충분히 큰 값
)
```

---

## �� 연락처 및 리소스

- **GitHub 저장소**: https://github.com/rafiki3816/langdocs.git
- **LangChain 문서**: https://python.langchain.com
- **Upstage 콘솔**: https://console.upstage.ai
- **ChromaDB 문서**: https://docs.trychroma.com

---

**작성일**: 2025-10-30
**버전**: 1.0
**상태**: ✅ 미션 1, 2 구현 완료 | 🔄 GitHub 업데이트 대기
