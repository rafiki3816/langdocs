# 🎯 LangChain 필수 학습 질문 30선

## 📚 기초 개념 (Basic Concepts) - 10문제

### 1. LangChain이란 무엇인가요?
**키워드**: LLM 애플리케이션, 프레임워크, 체인

### 2. LangChain의 주요 구성 요소는 무엇인가요?
**키워드**: Models, Prompts, Chains, Memory, Agents, Tools

### 3. LLM(Large Language Model)과 Chat Model의 차이점은 무엇인가요?
**키워드**: 텍스트 생성, 대화형 모델, 입출력 형식

### 4. Prompt Template이 필요한 이유는 무엇인가요?
**키워드**: 재사용성, 변수 치환, 구조화된 프롬프트

### 5. Chain이란 무엇이며, 왜 사용하나요?
**키워드**: 연속 작업, 모듈화, 파이프라인

### 6. Document Loader의 역할은 무엇인가요?
**키워드**: 데이터 로딩, 다양한 파일 형식, 전처리

### 7. Text Splitter는 왜 필요한가요?
**키워드**: 청킹, 토큰 제한, 오버랩, 컨텍스트 유지

### 8. Embedding이란 무엇이며, LangChain에서 어떻게 사용되나요?
**키워드**: 벡터화, 유사도 검색, 의미적 표현

### 9. Vector Store의 개념과 종류는 무엇인가요?
**키워드**: ChromaDB, Pinecone, FAISS, 벡터 데이터베이스

### 10. LangChain Expression Language(LCEL)란 무엇인가요?
**키워드**: 파이프 연산자, 체인 구성, 선언적 방식

## 🔧 중급 개념 (Intermediate Concepts) - 10문제

### 11. RAG(Retrieval-Augmented Generation) 시스템의 구조는 어떻게 되나요?
**키워드**: 검색, 증강, 생성, 컨텍스트 주입

### 12. ConversationBufferMemory와 ConversationSummaryMemory의 차이점은?
**키워드**: 전체 저장, 요약 저장, 토큰 효율성

### 13. RetrievalQA Chain의 작동 원리는 무엇인가요?
**키워드**: 질문, 검색, 컨텍스트, 답변 생성

### 14. Agent와 Tool의 관계는 무엇인가요?
**키워드**: 의사결정, 도구 선택, 실행, ReAct

### 15. Output Parser의 종류와 용도는?
**키워드**: 구조화된 출력, JSON, Pydantic, 검증

### 16. Callbacks는 어떤 경우에 사용하나요?
**키워드**: 모니터링, 로깅, 스트리밍, 비용 추적

### 17. Few-shot Prompting을 LangChain에서 구현하는 방법은?
**키워드**: 예시 선택, FewShotPromptTemplate, 동적 예시

### 18. MultiQueryRetriever의 장점은 무엇인가요?
**키워드**: 쿼리 확장, 다양한 관점, 검색 품질 향상

### 19. Contextual Compression이란 무엇인가요?
**키워드**: 문서 압축, 관련 정보 추출, 컨텍스트 최적화

### 20. LangChain에서 스트리밍 응답을 구현하는 방법은?
**키워드**: StreamingCallbackHandler, 실시간 출력, 사용자 경험

## 🚀 고급 개념 (Advanced Concepts) - 10문제

### 21. Hybrid Search(하이브리드 검색)를 구현하는 방법은?
**키워드**: 벡터 검색, 키워드 검색, BM25, 앙상블

### 22. Self-Query Retriever는 어떻게 작동하나요?
**키워드**: 자연어 쿼리, 메타데이터 필터링, 구조화된 쿼리

### 23. LangChain에서 Multi-Modal 처리는 어떻게 하나요?
**키워드**: 이미지, 텍스트, 오디오, 통합 처리

### 24. Agent의 ReAct 패턴이란 무엇인가요?
**키워드**: Reasoning, Acting, 관찰, 반복

### 25. LangGraph와 LangChain의 차이점은?
**키워드**: 그래프 기반, 상태 관리, 복잡한 워크플로우

### 26. Parent Document Retriever의 원리는?
**키워드**: 작은 청크 검색, 큰 컨텍스트 반환, 정확도

### 27. LangChain에서 Fine-tuning된 모델을 사용하는 방법은?
**키워드**: 커스텀 LLM, 래퍼 클래스, 통합

### 28. Ensemble Retriever를 구성하는 방법은?
**키워드**: 다중 검색기, 가중치, 결과 병합

### 29. LangChain의 보안 고려사항은 무엇인가요?
**키워드**: 프롬프트 인젝션, API 키 관리, 샌드박싱

### 30. Production 환경에서 LangChain 애플리케이션 최적화 방법은?
**키워드**: 캐싱, 배치 처리, 비동기, 모니터링

## 💡 실습 제안

각 질문에 대해:
1. **개념 이해**: 공식 문서 읽기
2. **코드 작성**: 실제 구현해보기
3. **실험**: 다양한 파라미터 테스트
4. **최적화**: 성능 개선 시도

## 🎯 학습 순서 권장

1. **1주차**: 질문 1-10 (기초 개념)
2. **2주차**: 질문 11-20 (중급 개념)
3. **3주차**: 질문 21-30 (고급 개념)
4. **4주차**: 통합 프로젝트 구현

## 📝 활용 방법

### 자가 평가
- 각 질문에 대해 3분 내에 설명할 수 있는가?
- 코드로 구현할 수 있는가?
- 실제 프로젝트에 적용할 수 있는가?

### 학습 체크리스트
- [ ] 개념 이해
- [ ] 코드 구현
- [ ] 예제 작성
- [ ] 문제 해결
- [ ] 최적화

## 🔍 추가 학습 리소스

1. **공식 문서**: https://python.langchain.com/docs/
2. **API 레퍼런스**: https://api.python.langchain.com/
3. **GitHub 예제**: https://github.com/langchain-ai/langchain
4. **커뮤니티**: Discord, Reddit r/LangChain

## 💬 현재 프로젝트에서 테스트 가능한 질문들

이 프로젝트의 코드를 통해 직접 학습할 수 있는 질문들:
- 질문 4: `prompts.py`에서 Prompt Template 확인
- 질문 8-9: `vector_database.py`에서 ChromaDB 사용법
- 질문 11: `retriever.py`에서 RAG 구현
- 질문 12: `conversation.py`에서 Memory 관리
- 질문 21: `retriever.py`의 HybridRetriever 클래스

---

**작성일**: 2024년 10월 28일
**용도**: LangChain 학습 로드맵 및 자가 평가