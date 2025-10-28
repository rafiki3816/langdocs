"""검색 시스템 모듈
하이브리드 검색 (벡터 + SQL) 구현"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun

from vector_database import VectorDatabase
from prompts import format_context


@dataclass
class SearchResult:
    """검색 결과를 담는 데이터 클래스"""
    document: Document
    score: float
    search_type: str  # "vector", "sql", "hybrid"


class HybridRetriever:
    """벡터 검색과 SQL 검색을 조합한 하이브리드 검색 클래스"""

    def __init__(
        self,
        vector_db_path: str = "./data/chroma_db",
        sqlite_db_path: str = "./data/langchain.db",
        collection_name: str = "langchain_docs"
    ):
        """
        HybridRetriever 초기화

        Args:
            vector_db_path: ChromaDB 경로
            sqlite_db_path: SQLite DB 경로
            collection_name: 컬렉션 이름
        """
        self.vector_db = VectorDatabase(vector_db_path, collection_name)
        self.vector_db.init_vectorstore()
        self.sqlite_db_path = sqlite_db_path

    def vector_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        벡터기반검색

        Args:
            query: 검색쿼리
            k: 반환할문서수
            score_threshold: 최소점수임계값

        Returns:
            SearchResult리스트
        """
        results = []

        # 벡터유사도검색
        docs_with_scores = self.vector_db.search_with_scores(query, k=k)

        for doc, score in docs_with_scores:
            # 점수임계값확인
            if score_threshold and score < score_threshold:
                continue

            results.append(SearchResult(
                document=doc,
                score=1.0 - score,  # ChromaDB거리를유사도로변환
                search_type="vector"
            ))

        return results

    def sql_search(
        self,
        query: str,
        k: int = 5
    ) -> List[SearchResult]:
        """
        SQL기반키워드검색

        Args:
            query: 검색쿼리
            k: 반환할문서수

        Returns:
            SearchResult리스트
        """
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        results = []

        try:
            # 키워드검색쿼리
            sql_query = """
            SELECT doc_id, title, url, category, content,
            (CASE
                WHEN title LIKE ? THEN 3
                WHEN content LIKE ? THEN 1
                ELSE 0
            END) as relevance_score
            FROM documents
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT ?
            """

            search_term = f"%{query}%"
            cursor.execute(sql_query, (
                search_term, search_term,
                search_term, search_term,
                k
            ))

            rows = cursor.fetchall()

            for row in rows:
                doc_id, title, url, category, content, score = row

                doc = Document(
                    page_content=content,
                    metadata={
                        "doc_id": doc_id,
                        "title": title,
                        "url": url,
                        "category": category,
                        "source": "sql_search"
                    }
                )

                results.append(SearchResult(
                    document=doc,
                    score=score / 3.0,  # 정규화
                    search_type="sql"
                ))

        except Exception as e:
            print(f"SQL검색중오류발생: {e}")

        finally:
            conn.close()

        return results

    def sql_search_by_category(
        self,
        query: str,
        category: str,
        k: int = 5
    ) -> List[SearchResult]:
        """
        특정카테고리로필터링된SQL검색

        Args:
            query: 검색쿼리
            category: 카테고리
            k: 반환할문서수

        Returns:
            SearchResult리스트
        """
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        results = []

        try:
            sql_query = """
            SELECT doc_id, title, url, category, content
            FROM documents
            WHERE category = ? AND (title LIKE ? OR content LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
            """

            search_term = f"%{query}%"
            cursor.execute(sql_query, (category, search_term, search_term, k))

            rows = cursor.fetchall()

            for row in rows:
                doc_id, title, url, category, content = row

                doc = Document(
                    page_content=content,
                    metadata={
                        "doc_id": doc_id,
                        "title": title,
                        "url": url,
                        "category": category,
                        "source": "sql_category_search"
                    }
                )

                results.append(SearchResult(
                    document=doc,
                    score=0.8,  # 카테고리일치기본점수
                    search_type="sql"
                ))

        except Exception as e:
            print(f"SQL카테고리검색중오류발생: {e}")

        finally:
            conn.close()

        return results

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_weight: float = 0.7,
        sql_weight: float = 0.3
    ) -> List[SearchResult]:
        """
        하이브리드검색(벡터+SQL)

        Args:
            query: 검색쿼리
            k: 반환할문서수
            vector_weight: 벡터검색가중치
            sql_weight: SQL검색가중치

        Returns:
            SearchResult리스트
        """
        # 두검색방법에서각각더많은문서를수집
        vector_results = self.vector_search(query, k=k * 2)
        sql_results = self.sql_search(query, k=k * 2)

        # 결과수집및병합준비
        combined_results = {}

        # 벡터검색결과추가
        for result in vector_results:
            doc_id = result.document.metadata.get("doc_id", str(id(result.document)))
            combined_results[doc_id] = SearchResult(
                document=result.document,
                score=result.score * vector_weight,
                search_type="hybrid"
            )

        # SQL검색결과추가및수집
        for result in sql_results:
            doc_id = result.document.metadata.get("doc_id", str(id(result.document)))

            if doc_id in combined_results:
                # 이미존재하면점수누적
                combined_results[doc_id].score += result.score * sql_weight
            else:
                combined_results[doc_id] = SearchResult(
                    document=result.document,
                    score=result.score * sql_weight,
                    search_type="hybrid"
                )

        # 점수기준으로정렬후상위k개반환
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x.score,
            reverse=True
        )

        return sorted_results[:k]

    def rerank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """
        검색결과재정렬

        Args:
            results: 검색결과리스트
            query: 원본쿼리

        Returns:
            재정렬된결과리스트
        """
        # 쿼리키워드추출
        query_keywords = set(query.lower().split())

        for result in results:
            # 제목일치보너스
            title = result.document.metadata.get("title", "").lower()
            title_match_score = sum(1 for kw in query_keywords if kw in title)

            # 카테고리보너스
            category = result.document.metadata.get("category", "")
            category_bonus = 0.1 if category in ["tutorials", "how_to"] else 0

            # 최종점수계산
            result.score = result.score + (title_match_score * 0.1) + category_bonus

        # 재정렬
        return sorted(results, key=lambda x: x.score, reverse=True)

    def get_relevant_documents(
        self,
        query: str,
        k: int = 5,
        search_type: str = "hybrid"
    ) -> List[Document]:
        """
        관련문서를검색하여반환

        Args:
            query: 검색쿼리
            k: 반환할문서수
            search_type: 검색타입("vector", "sql", "hybrid")

        Returns:
            Document리스트
        """
        if search_type == "vector":
            results = self.vector_search(query, k=k)
        elif search_type == "sql":
            results = self.sql_search(query, k=k)
        elif search_type == "hybrid":
            results = self.hybrid_search(query, k=k)
        else:
            raise ValueError(f"지원하지않는검색타입: {search_type}")

        # 재정렬
        results = self.rerank_results(results, query)

        # Document객체만반환
        return [result.document for result in results]


class LangChainRetriever(BaseRetriever):
    """LangChainBaseRetriever를상속한커스텀Retriever"""

    retriever: HybridRetriever
    k: int = 5
    search_type: str = "hybrid"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever = HybridRetriever()

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """검색실행"""
        return self.retriever.get_relevant_documents(
            query,
            k=self.k,
            search_type=self.search_type
        )

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """비동기검색실행"""
        # 현재는동기구현사용
        return self._get_relevant_documents(query, run_manager=run_manager)


# 편의함수
def create_retriever(
    search_type: str = "hybrid",
    k: int = 5
) -> LangChainRetriever:
    """
    Retriever인스턴스를생성합니다.

    Args:
        search_type: 검색타입
        k: 반환할문서수

    Returns:
        LangChainRetriever인스턴스
    """
    return LangChainRetriever(k=k, search_type=search_type)


def search_documents(
    query: str,
    k: int = 5,
    search_type: str = "hybrid"
) -> List[Document]:
    """
    문서를검색합니다.

    Args:
        query: 검색쿼리
        k: 반환할문서수
        search_type: 검색타입

    Returns:
        Document리스트
    """
    retriever = HybridRetriever()
    return retriever.get_relevant_documents(query, k=k, search_type=search_type)


def format_search_results(
    results: List[Document],
    max_length: int = 3000
) -> str:
    """
    검색결과를포맷팅합니다.

    Args:
        results: 검색결과
        max_length: 최대길이

    Returns:
        포맷팅된문자열
    """
    return format_context(results, max_length)


if __name__ == "__main__":
    # 모듈테스트
    print("=== Retriever모듈테스트\n")

    # Retriever초기화
    retriever = HybridRetriever()

    # 테스트쿼리
    test_query = "LangChain LCEL 사용법"

    print(f"테스트쿼리: '{test_query}'\n")

    # 1. 벡터검색테스트
    print("1. 벡터검색")
    try:
        vector_results = retriever.vector_search(test_query, k=3)
        print(f"검색된결과: {len(vector_results)}개")
        for i, result in enumerate(vector_results[:2], 1):
            print(f"결과{i}(점수: {result.score:.3f})")
            print(f"내용: {result.document.page_content[:100]}...")
    except Exception as e:
        print(f"벡터DB가없습니다. data_collector.py로데이터를먼저수집하세요.")

    # 2. SQL검색테스트
    print("\n2. SQL검색")
    try:
        sql_results = retriever.sql_search(test_query, k=3)
        print(f"검색된결과: {len(sql_results)}개")
        if sql_results:
            for i, result in enumerate(sql_results[:2], 1):
                print(f"결과{i}: {result.document.metadata.get('title', 'Untitled')}")
        else:
            print(f"SQLDB가없습니다. data_collector.py로데이터를먼저수집하세요.")
    except Exception as e:
        print(f"오류발생: {e}")

    # 3. 하이브리드검색테스트
    print("\n3. 하이브리드검색")
    try:
        hybrid_results = retriever.hybrid_search(test_query, k=3)
        print(f"검색된결과: {len(hybrid_results)}개")
        for i, result in enumerate(hybrid_results, 1):
            print(f"결과{i}(점수: {result.score:.3f}, 타입: {result.search_type})")
    except Exception as e:
        print(f"오류발생: {e}")

    # 4. LangChainRetriever테스트
    print("\n4. LangChainRetriever")
    try:
        lc_retriever = create_retriever()
        docs = lc_retriever.get_relevant_documents(test_query)
        print(f"검색된문서: {len(docs)}개")
    except Exception as e:
        print(f"오류발생: {e}")

    print("\n=== 테스트완료!")
