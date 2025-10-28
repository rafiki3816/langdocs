# 데이터베이스 선택 가이드

## 🎯 프로젝트 요구사항

### RAG 챗봇에 필요한 데이터베이스
1. **SQL 데이터베이스**: 메타데이터, 로그, 사용자 정보 저장
2. **벡터 데이터베이스**: 임베딩 저장 및 유사도 검색

---

## 💾 SQL 데이터베이스 옵션

### 1. 로컬 개발 옵션

#### SQLite (내장형)
```python
DATABASE_URL = "sqlite:///./chatbot.db"
```
- ✅ **장점**: 설치 불필요, 파일 기반, 가장 간단
- ❌ **단점**: 동시 접속 제한, 프로덕션 부적합
- 💡 **추천**: 초기 개발 및 테스트용

#### MySQL (로컬 설치)
```bash
# macOS
brew install mysql
brew services start mysql

# 데이터베이스 생성
mysql -u root -p
CREATE DATABASE langchain_chatbot;
```
```python
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/langchain_chatbot"
```
- ✅ **장점**: 무료, 널리 사용됨
- ❌ **단점**: 로컬 설치/관리 필요

#### PostgreSQL (로컬 설치)
```bash
# macOS
brew install postgresql
brew services start postgresql

# 데이터베이스 생성
createdb langchain_chatbot
```
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/langchain_chatbot"
```
- ✅ **장점**: 고급 기능, JSON 지원 우수
- ❌ **단점**: 설정 복잡

---

### 2. 클라우드 서비스 옵션 (무료 티어)

#### Supabase (PostgreSQL)
```python
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```
- ✅ **무료 제공**: 500MB 스토리지, 2개 프로젝트
- ✅ **추가 기능**: 인증, 실시간, 스토리지 포함
- 🌐 **URL**: https://supabase.com
- 💡 **추천도**: ⭐⭐⭐⭐⭐

#### Neon (PostgreSQL)
```python
DATABASE_URL = "postgresql://[user]:[password]@[endpoint].neon.tech/[database]?sslmode=require"
```
- ✅ **무료 제공**: 3GB 스토리지, 무제한 프로젝트
- ✅ **특징**: 서버리스, 자동 스케일링
- 🌐 **URL**: https://neon.tech
- 💡 **추천도**: ⭐⭐⭐⭐⭐

#### PlanetScale (MySQL)
```python
DATABASE_URL = "mysql://[username]:[password]@[host]/[database]?ssl={"rejectUnauthorized":true}"
```
- ✅ **무료 제공**: 5GB 스토리지, 1개 데이터베이스
- ✅ **특징**: 서버리스, 자동 샤딩
- 🌐 **URL**: https://planetscale.com
- 💡 **추천도**: ⭐⭐⭐⭐

#### Aiven (MySQL/PostgreSQL)
```python
DATABASE_URL = "mysql://avnadmin:[password]@[host]:[port]/defaultdb?ssl-mode=REQUIRED"
```
- ✅ **무료 크레딧**: $300 (1개월)
- ✅ **특징**: 다양한 DB 지원
- 🌐 **URL**: https://aiven.io
- 💡 **추천도**: ⭐⭐⭐

#### Railway (PostgreSQL/MySQL)
```python
DATABASE_URL = "postgresql://postgres:[password]@[host]:[port]/railway"
```
- ✅ **무료 제공**: $5 크레딧/월
- ✅ **특징**: 간단한 배포
- 🌐 **URL**: https://railway.app
- 💡 **추천도**: ⭐⭐⭐

---

## 🔍 벡터 데이터베이스 옵션

### 1. 로컬/자체 호스팅

#### ChromaDB (기본 선택)
```python
import chromadb
client = chromadb.PersistentClient(path="./data/chroma_db")
```
- ✅ **장점**: 로컬 파일 기반, 설치 간단
- ✅ **비용**: 무료
- 💡 **추천**: 개발 및 중소규모용

#### Qdrant (Docker)
```bash
docker run -p 6333:6333 qdrant/qdrant
```
```python
from qdrant_client import QdrantClient
client = QdrantClient("localhost", port=6333)
```
- ✅ **장점**: 고성능, REST API
- ❌ **단점**: Docker 필요

### 2. 클라우드 서비스

#### Pinecone
```python
import pinecone
pinecone.init(api_key="YOUR_API_KEY")
```
- ✅ **무료 제공**: 1개 인덱스, 100K 벡터
- 🌐 **URL**: https://pinecone.io
- 💡 **추천도**: ⭐⭐⭐⭐

#### Weaviate Cloud
```python
import weaviate
client = weaviate.Client("https://[cluster-name].weaviate.network")
```
- ✅ **무료 제공**: 14일 체험
- 🌐 **URL**: https://weaviate.io
- 💡 **추천도**: ⭐⭐⭐

#### Qdrant Cloud
```python
from qdrant_client import QdrantClient
client = QdrantClient(url="https://[cluster].qdrant.io", api_key="YOUR_API_KEY")
```
- ✅ **무료 제공**: 1GB 메모리
- 🌐 **URL**: https://qdrant.tech
- 💡 **추천도**: ⭐⭐⭐⭐

---

## 🎯 추천 조합

### 🥇 개발 환경 (가장 간단)
```python
# SQL: SQLite
DATABASE_URL = "sqlite:///./chatbot.db"

# Vector: ChromaDB (로컬)
CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"
```
**장점**: 설치 불필요, 즉시 시작 가능

### 🥈 프로덕션 준비 (무료)
```python
# SQL: Supabase 또는 Neon
DATABASE_URL = "postgresql://..." # Supabase/Neon URL

# Vector: ChromaDB (로컬) 또는 Pinecone
PINECONE_API_KEY = "your-api-key"
```
**장점**: 확장 가능, 프로덕션 준비

### 🥉 엔터프라이즈 (유료)
```python
# SQL: AWS RDS, Google Cloud SQL
# Vector: Pinecone Pro, Weaviate Enterprise
```

---

## 📝 의사결정 체크리스트

### SQL 데이터베이스 선택 기준
- [ ] 로컬 개발만? → **SQLite**
- [ ] 팀 협업 필요? → **클라우드 서비스**
- [ ] PostgreSQL 선호? → **Supabase** 또는 **Neon**
- [ ] MySQL 선호? → **PlanetScale**
- [ ] 완전 무료 필요? → **Supabase** (가장 관대한 무료 티어)

### 벡터 데이터베이스 선택 기준
- [ ] 가장 간단한 설정? → **ChromaDB**
- [ ] 클라우드 선호? → **Pinecone**
- [ ] 고성능 필요? → **Qdrant**

---

## 🚀 빠른 시작 가이드

### 옵션 1: 가장 빠른 시작 (5분)
```bash
# .env 파일 수정
DATABASE_URL=sqlite:///./chatbot.db
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# 바로 시작!
python scripts/init_db.py
```

### 옵션 2: Supabase 설정 (15분)
1. https://supabase.com 가입
2. 새 프로젝트 생성
3. Settings > Database에서 연결 문자열 복사
4. `.env` 파일 업데이트
```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### 옵션 3: Neon 설정 (10분)
1. https://neon.tech 가입
2. 새 프로젝트 생성
3. Connection string 복사
4. `.env` 파일 업데이트
```bash
DATABASE_URL=postgresql://[user]:[password]@[endpoint].neon.tech/neondb?sslmode=require
```

---

## 💰 비용 비교

| 서비스 | SQL 무료 제공 | 벡터 DB | 월 예상 비용 |
|--------|--------------|---------|-------------|
| **로컬 (SQLite + ChromaDB)** | 무제한 | 무제한 | $0 |
| **Supabase + ChromaDB** | 500MB | 로컬 | $0 |
| **Neon + ChromaDB** | 3GB | 로컬 | $0 |
| **PlanetScale + Pinecone** | 5GB | 100K 벡터 | $0 |
| **Railway + Pinecone** | $5 크레딧 | 100K 벡터 | ~$5 |

---

## 🎯 최종 추천

### 현재 프로젝트 단계를 고려한 추천:

#### **1단계: 개발 (지금)**
```python
# SQLite + ChromaDB (로컬)
DATABASE_URL = "sqlite:///./chatbot.db"
CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"
```
- ✅ 즉시 시작 가능
- ✅ 설치/설정 불필요
- ✅ 비용 없음

#### **2단계: 테스트 (Phase 5 이후)**
```python
# Supabase + ChromaDB
DATABASE_URL = "postgresql://..."  # Supabase
CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"
```
- ✅ 실제 PostgreSQL 환경
- ✅ 팀 협업 가능
- ✅ 여전히 무료

#### **3단계: 프로덕션 (배포 시)**
```python
# Supabase/Neon + Pinecone
DATABASE_URL = "postgresql://..."  # Supabase/Neon
PINECONE_API_KEY = "..."
```
- ✅ 확장 가능
- ✅ 관리형 서비스
- ✅ 무료 티어로 시작

---

## 📌 결정하기

### 질문:
1. **지금 바로 개발을 시작하시겠습니까?**
   - Yes → SQLite + ChromaDB (로컬)
   - No → 클라우드 서비스 설정

2. **팀과 협업이 필요하신가요?**
   - Yes → Supabase 또는 Neon
   - No → SQLite 가능

3. **PostgreSQL vs MySQL 선호도는?**
   - PostgreSQL → Supabase, Neon
   - MySQL → PlanetScale
   - 상관없음 → SQLite (개발용)

---

**추천**: 현재는 **SQLite + ChromaDB**로 시작하고, 나중에 필요시 마이그레이션하는 것이 가장 효율적입니다!

**작성일**: 2025-10-28
**프로젝트**: LangChain Documentation Chatbot