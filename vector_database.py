"""벡터 데이터베이스 모듈
ChromaDB를 사용한 문서 임베딩 저장 및 검색"""

import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_core.embeddings import Embeddings

from llm import get_embeddings


class VectorDatabase:
    """ChromaDB 벡터 데이터베이스 관리 클래스"""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "langchain_docs"
    ):
        """
        VectorDatabase 초기화

        Args:
            persist_directory: ChromaDB 저장 디렉토리
            collection_name: 컬렉션 이름
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = get_embeddings()
        self.vectorstore = None

        # 디렉토리 생성
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

    def init_vectorstore(self, reset: bool = False) -> Chroma:
        """
        벡터 저장소를 초기화합니다.

        Args:
            reset: True일 경우 기존 데이터를 삭제 후 재생성

        Returns:
            Chroma 벡터 저장소 인스턴스
        """
        if reset and os.path.exists(self.persist_directory):
            print(f"기존 벡터 DB 삭제: {self.persist_directory}")
            shutil.rmtree(self.persist_directory)
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        print(f"벡터 저장소 초기화 완료: {self.collection_name}")
        return self.vectorstore

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[str]:
        """
        문서를 벡터 저장소에 추가합니다.

        Args:
            documents: 추가할 문서 리스트
            batch_size: 배치 크기
            show_progress: 진행률 표시 여부

        Returns:
            추가된 문서 ID 리스트
        """
        if not self.vectorstore:
            self.init_vectorstore()

        all_ids = []
        total_docs = len(documents)

        print(f"총 {total_docs}개 문서 추가 중...")

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]

            if show_progress:
                progress = min(i + batch_size, total_docs)
                print(f"진행률: {progress}/{total_docs} ({progress*100//total_docs}%)")

            ids = self.vectorstore.add_documents(batch)
            all_ids.extend(ids)

        # 저장
        self.vectorstore.persist()
        print(f"총 {len(all_ids)}개 문서 추가 완료")

        return all_ids

    def search_similar(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Document]:
        """
        유사한 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            score_threshold: 최소 유사도 점수

        Returns:
            유사한 문서 리스트
        """
        if not self.vectorstore:
            self.init_vectorstore()

        search_kwargs = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        if score_threshold is not None:
            # 점수 포함 검색
            results = self.vectorstore.similarity_search_with_score(
                query,
                **search_kwargs
            )
            # 점수 임계값 이상인 것만 반환
            filtered_results = [
                doc for doc, score in results
                if score >= score_threshold
            ]
            return filtered_results
        else:
            # 일반 검색
            return self.vectorstore.similarity_search(query, **search_kwargs)

    def search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        유사한 문서를 점수와 함께 검색합니다.

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터

        Returns:
            (문서, 점수) 튜플 리스트
        """
        if not self.vectorstore:
            self.init_vectorstore()

        search_kwargs = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        return self.vectorstore.similarity_search_with_score(query, **search_kwargs)

    def delete_documents(self, ids: List[str]) -> bool:
        """
        문서를 삭제합니다.

        Args:
            ids: 삭제할 문서 ID 리스트

        Returns:
            삭제 성공 여부
        """
        if not self.vectorstore:
            print("벡터 저장소가 초기화되지 않았습니다.")
            return False

        try:
            self.vectorstore.delete(ids)
            self.vectorstore.persist()
            print(f"총 {len(ids)}개 문서 삭제 완료")
            return True
        except Exception as e:
            print(f"문서 삭제 중 오류 발생: {e}")
            return False

    def get_retriever(self, **kwargs):
        """
        Retriever 인스턴스를 반환합니다.

        Args:
            **kwargs: Retriever 설정 파라미터

        Returns:
            VectorStoreRetriever 인스턴스
        """
        if not self.vectorstore:
            self.init_vectorstore()

        return self.vectorstore.as_retriever(**kwargs)

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        컬렉션 통계 정보를 반환합니다.

        Returns:
            통계 정보 딕셔너리
        """
        if not self.vectorstore:
            self.init_vectorstore()

        try:
            # ChromaDB 클라이언트에 직접 접근
            client = chromadb.PersistentClient(path=self.persist_directory)
            collection = client.get_collection(name=self.collection_name)

            stats = {
                "collection_name": self.collection_name,
                "document_count": collection.count(),
                "persist_directory": self.persist_directory,
                "embedding_dimension": 4096  # Solar 임베딩 차원
            }
            return stats
        except Exception as e:
            print(f"통계 조회 중 오류 발생: {e}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "error": str(e)
            }


# 편의 함수들
def init_chromadb(
    persist_directory: str = "./data/chroma_db",
    collection_name: str = "langchain_docs",
    reset: bool = False
) -> VectorDatabase:
    """
    ChromaDB를 초기화하고 VectorDatabase 인스턴스를 반환합니다.

    Args:
        persist_directory: 저장 디렉토리
        collection_name: 컬렉션 이름
        reset: 초기화 여부

    Returns:
        VectorDatabase 인스턴스
    """
    vdb = VectorDatabase(persist_directory, collection_name)
    vdb.init_vectorstore(reset=reset)
    return vdb


def add_documents(
    documents: List[Document],
    persist_directory: str = "./data/chroma_db",
    collection_name: str = "langchain_docs"
) -> List[str]:
    """
    문서를 벡터 데이터베이스에 추가합니다.

    Args:
        documents: 추가할 문서 리스트
        persist_directory: 저장 디렉토리
        collection_name: 컬렉션 이름

    Returns:
        추가된 문서 ID 리스트
    """
    vdb = VectorDatabase(persist_directory, collection_name)
    return vdb.add_documents(documents)


def search_similar(
    query: str,
    k: int = 5,
    persist_directory: str = "./data/chroma_db",
    collection_name: str = "langchain_docs"
) -> List[Document]:
    """
    유사한 문서를 검색합니다.

    Args:
        query: 검색 쿼리
        k: 반환할 문서 수
        persist_directory: 저장 디렉토리
        collection_name: 컬렉션 이름

    Returns:
        유사한 문서 리스트
    """
    vdb = VectorDatabase(persist_directory, collection_name)
    return vdb.search_similar(query, k=k)


if __name__ == "__main__":
    # 테스트 코드
    print("=== Vector Database 테스트 코드\n")

    # 1. 초기화 테스트
    print("1단계: 벡터 DB 초기화 테스트")
    vdb = init_chromadb(reset=True)

    # 2. 문서 추가 테스트
    print("\n2단계: 문서 추가 테스트")
    test_docs = [
        Document(
            page_content="LangChain은 대규모 언어 모델(LLM)을 활용한 애플리케이션 개발을 위한 프레임워크입니다.",
            metadata={"source": "intro", "category": "concept"}
        ),
        Document(
            page_content="LangChain은 체인(Chain), 에이전트(Agent), 도구(Tools) 등의 구성 요소들을 제공합니다.",
            metadata={"source": "components", "category": "guide"}
        ),
        Document(
            page_content="LCEL(LangChain Expression Language)은 선언적으로 복잡한 체인을 쉽게 구성할 수 있게 합니다.",
            metadata={"source": "lcel", "category": "tutorial"}
        ),
    ]
    ids = vdb.add_documents(test_docs)
    print(f"추가된 문서 ID: {ids[:2]}...")

    # 3. 검색 테스트
    print("\n3단계: 유사도 검색 테스트")
    query = "LangChain의 구성 요소에 대해 알려주세요"
    results = vdb.search_similar(query, k=2)
    for i, doc in enumerate(results, 1):
        print(f"검색 결과 {i}: {doc.page_content[:50]}...")
        print(f"  메타데이터: {doc.metadata}")

    # 4. 통계 조회 테스트
    print("\n4단계: 컬렉션 통계")
    stats = vdb.get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n모든 테스트 완료!")
