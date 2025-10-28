# 📁 웹크롤링 데이터 저장 구조 가이드

## 🗂️ 전체 저장 구조

```
langChainDocs/
└── data/                        # 모든 데이터 저장 루트
    ├── langchain.db            # SQLite 데이터베이스 (메타데이터)
    ├── raw/                    # 원본 JSON 파일
    │   ├── docs_introduction.json
    │   ├── docs_concepts.json
    │   └── ...
    ├── chroma_db/              # 벡터 데이터베이스
    │   ├── chroma.sqlite3      # ChromaDB 인덱스
    │   └── [collection_id]/    # 임베딩 데이터
    ├── processed/              # 처리된 데이터 (선택)
    └── embeddings/             # 캐시된 임베딩 (선택)
```

## 💾 데이터가 저장되는 3곳

### 1️⃣ **SQLite 데이터베이스** (`data/langchain.db`)

**저장 내용:**
- 📄 문서 메타데이터 (제목, URL, 카테고리)
- 💬 대화 기록
- 📊 평가 결과
- 🔗 문서 간 관계

**테이블 구조:**
```sql
documents       # 문서 정보
├── doc_id      # 고유 ID
├── title       # 제목
├── url         # 원본 URL
├── content     # 텍스트 내용
├── category    # 카테고리
└── created_at  # 수집 시간

code_examples   # 코드 예제
├── doc_id      # 문서 참조
├── code        # 코드 내용
└── language    # 언어

conversations   # 대화 세션
messages       # 대화 메시지
evaluations    # 평가 결과
```

**확인 방법:**
```bash
# DB 내용 확인
sqlite3 data/langchain.db "SELECT COUNT(*) FROM documents;"
sqlite3 data/langchain.db "SELECT title, category FROM documents;"
```

### 2️⃣ **원본 JSON 파일** (`data/raw/`)

**저장 내용:**
- 🌐 크롤링한 웹페이지 전체 내용
- 📝 구조화된 JSON 형식
- 🏷️ 모든 메타데이터 포함

**파일명 규칙:**
- URL 기반: `docs_introduction.json`
- 경로 기반: `docs_get_started_quickstart.json`

**JSON 구조:**
```json
{
  "doc_id": "docs_introduction",
  "title": "Introduction | LangChain",
  "url": "https://python.langchain.com/docs/introduction",
  "category": "introduction",
  "content": "전체 페이지 텍스트...",
  "metadata": {
    "timestamp": "2024-10-28T20:34:00",
    "source": "web_crawler"
  }
}
```

**확인 방법:**
```bash
# JSON 파일 목록
ls -la data/raw/

# 파일 내용 미리보기
cat data/raw/docs_introduction.json | python3 -m json.tool | head -20
```

### 3️⃣ **벡터 데이터베이스** (`data/chroma_db/`)

**저장 내용:**
- 🔢 문서 임베딩 벡터 (4096차원)
- 🔍 검색 인덱스
- 🏷️ 청크별 메타데이터

**구조:**
```
chroma_db/
├── chroma.sqlite3              # 인덱스 및 메타데이터
└── 22702f99-6e14-.../         # 컬렉션 ID
    ├── data_level0.bin         # 임베딩 데이터
    ├── header.bin              # 헤더 정보
    ├── index_metadata.pickle   # 인덱스 메타데이터
    └── ...
```

**확인 방법:**
```bash
# ChromaDB 상태 확인
python3 -c "
from vector_database import VectorDatabase
vdb = VectorDatabase()
vdb.init_vectorstore()
stats = vdb.get_statistics()
print(f'저장된 벡터: {stats[\"document_count\"]}개')
print(f'컬렉션: {stats[\"collection_name\"]}')
"
```

## 📊 데이터 흐름

```
웹페이지 (URL)
    ↓ [크롤링]
원본 HTML
    ↓ [파싱]
JSON 파일 (data/raw/)
    ↓ [저장]
SQLite DB (data/langchain.db)
    ↓ [청킹]
문서 청크들
    ↓ [임베딩]
벡터 DB (data/chroma_db/)
```

## 📈 저장 용량 관리

### 현재 사용량 확인
```bash
# 전체 용량
du -sh data/

# 각 폴더별 용량
du -sh data/*

# 파일 개수
find data -type f | wc -l
```

### 예상 용량
| 문서 수 | SQLite | JSON | ChromaDB | 총 용량 |
|---------|--------|------|----------|---------|
| 10개 | ~100KB | ~200KB | ~500KB | ~1MB |
| 50개 | ~500KB | ~1MB | ~2.5MB | ~4MB |
| 100개 | ~1MB | ~2MB | ~5MB | ~8MB |
| 500개 | ~5MB | ~10MB | ~25MB | ~40MB |

## 🔍 데이터 조회 방법

### 1. SQLite 데이터 조회
```python
import sqlite3
conn = sqlite3.connect('data/langchain.db')
cursor = conn.cursor()

# 문서 목록
cursor.execute("SELECT title, url, category FROM documents")
for row in cursor.fetchall():
    print(row)

# 카테고리별 통계
cursor.execute("SELECT category, COUNT(*) FROM documents GROUP BY category")
for category, count in cursor.fetchall():
    print(f"{category}: {count}개")
```

### 2. JSON 파일 조회
```python
import json
import os

# 모든 JSON 파일 읽기
for filename in os.listdir('data/raw/'):
    if filename.endswith('.json'):
        with open(f'data/raw/{filename}', 'r') as f:
            data = json.load(f)
            print(f"제목: {data['title']}")
            print(f"URL: {data['url']}")
            print(f"내용 길이: {len(data['content'])} 글자")
            print("---")
```

### 3. 벡터 DB 조회
```python
from vector_database import VectorDatabase

vdb = VectorDatabase()
vdb.init_vectorstore()

# 유사도 검색
results = vdb.search_similar("LangChain이란?", k=3)
for doc in results:
    print(f"제목: {doc.metadata.get('title', 'Unknown')}")
    print(f"내용: {doc.page_content[:100]}...")
    print("---")
```

## 🗑️ 데이터 정리 방법

### 모든 데이터 삭제 (초기화)
```bash
# 주의: 모든 데이터가 삭제됩니다!
rm -rf data/raw/*.json
rm -rf data/chroma_db/*
rm data/langchain.db

# 다시 초기화
python3 init_db.py
```

### 특정 카테고리만 삭제
```python
import sqlite3
conn = sqlite3.connect('data/langchain.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM documents WHERE category = 'tutorials'")
conn.commit()
```

## 💡 팁과 주의사항

### 추천 사항
1. **정기 백업**: 중요 데이터는 정기적으로 백업
2. **용량 모니터링**: 1000개 이상 문서 시 용량 확인
3. **중복 제거**: 같은 URL 재수집 방지

### 주의 사항
1. **ChromaDB 파일 직접 수정 금지**: 인덱스 손상 위험
2. **SQLite 트랜잭션**: 대량 작업 시 트랜잭션 사용
3. **JSON 파일명**: 특수문자 제거된 URL 기반

## 🔄 백업 및 복원

### 백업
```bash
# 전체 백업
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# DB만 백업
cp data/langchain.db backup_langchain_$(date +%Y%m%d).db
```

### 복원
```bash
# 전체 복원
tar -xzf backup_20241028.tar.gz

# DB만 복원
cp backup_langchain_20241028.db data/langchain.db
```

## 📍 현재 상태

```bash
# 현재 저장된 데이터
- SQLite DB: 98KB (3개 문서)
- JSON 파일: 34KB (3개 파일)
- ChromaDB: 213KB (3개 문서 벡터)
- 총 용량: 약 345KB
```

---

**요약**: 웹크롤링 데이터는 3곳에 저장됩니다:
1. **SQLite** (`data/langchain.db`) - 메타데이터와 구조화된 정보
2. **JSON** (`data/raw/`) - 원본 크롤링 데이터
3. **ChromaDB** (`data/chroma_db/`) - 검색용 벡터 임베딩

모든 데이터는 `data/` 폴더 아래에 체계적으로 저장되며, 필요시 쉽게 백업/복원 가능합니다.