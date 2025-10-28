#!/usr/bin/env python3
"""
LangChain RAG 챗봇 - 간단한 실행 파일
"""

import os
import sys
import argparse
from datetime import datetime

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='LangChain RAG 챗봇')
    parser.add_argument('--mode', choices=['chat', 'collect', 'evaluate', 'web'],
                       default='chat', help='실행 모드')
    parser.add_argument('--question', type=str, help='단일 질문 (chat 모드)')
    parser.add_argument('--urls', nargs='+', help='수집할 URL 목록 (collect 모드)')

    args = parser.parse_args()

    print("\n🤖 LangChain RAG 챗봇 v1.0")
    print("=" * 50)

    if args.mode == 'chat':
        # 채팅 모드
        from llm import get_llm
        from vector_database import VectorDatabase
        from retriever import HybridRetriever

        print("채팅 모드를 시작합니다...")

        # LLM 초기화
        llm = get_llm()

        # 벡터 DB 초기화
        vdb = VectorDatabase()
        vdb.init_vectorstore()

        # Retriever 초기화
        retriever = HybridRetriever(vdb)

        if args.question:
            # 단일 질문 처리
            print(f"\n질문: {args.question}")

            # 문서 검색
            docs = retriever.search(args.question, k=3)

            # 컨텍스트 생성
            context = "\n\n".join([doc.page_content[:500] for doc in docs])

            # LLM으로 답변 생성
            prompt = f"""다음 컨텍스트를 바탕으로 질문에 답하세요.

컨텍스트:
{context}

질문: {args.question}

답변:"""

            response = llm.invoke(prompt)
            print(f"\n답변: {response.content if hasattr(response, 'content') else response}")

        else:
            # 대화형 모드
            print("\n대화를 시작합니다. 종료하려면 'exit'를 입력하세요.\n")

            while True:
                question = input("질문> ").strip()

                if question.lower() in ['exit', 'quit', '종료']:
                    print("챗봇을 종료합니다.")
                    break

                if not question:
                    continue

                # 문서 검색
                docs = retriever.search(question, k=3)

                # 컨텍스트 생성
                context = "\n\n".join([doc.page_content[:500] for doc in docs])

                # LLM으로 답변 생성
                prompt = f"""다음 컨텍스트를 바탕으로 질문에 답하세요.

컨텍스트:
{context}

질문: {question}

답변:"""

                response = llm.invoke(prompt)
                print(f"\n답변: {response.content if hasattr(response, 'content') else response}\n")

    elif args.mode == 'collect':
        # 문서 수집 모드
        from data_collector import LangChainDataCollector

        print("문서 수집 모드를 시작합니다...")

        collector = LangChainDataCollector()

        if args.urls:
            urls = args.urls
        else:
            urls = collector.get_sample_urls()[:5]

        print(f"수집할 URL: {len(urls)}개")
        documents = collector.collect_documents(urls=urls, max_pages=len(urls))

        if documents:
            print(f"✅ {len(documents)}개 문서 수집 완료")

            # 벡터 DB에 저장
            from vector_database import VectorDatabase
            vdb = VectorDatabase()
            vdb.init_vectorstore()

            # 청크 분할
            chunked_docs = collector.chunk_documents(documents)

            # 벡터 DB에 추가
            vdb.add_documents(chunked_docs)
            print(f"✅ {len(chunked_docs)}개 청크 저장 완료")
        else:
            print("❌ 문서 수집 실패")

    elif args.mode == 'evaluate':
        # 평가 모드
        print("평가 모드를 시작합니다...")

        # 간단한 테스트
        test_questions = [
            "LangChain이 무엇인가요?",
            "체인(Chain)은 무엇인가요?",
            "에이전트(Agent)는 어떻게 작동하나요?"
        ]

        from llm import get_llm
        from vector_database import VectorDatabase
        from retriever import HybridRetriever
        import time

        llm = get_llm()
        vdb = VectorDatabase()
        vdb.init_vectorstore()
        retriever = HybridRetriever(vdb)

        print(f"\n{len(test_questions)}개 질문 평가 중...")

        for i, question in enumerate(test_questions, 1):
            print(f"\n[{i}/{len(test_questions)}] {question}")

            start_time = time.time()

            # 문서 검색
            docs = retriever.search(question, k=3)

            # 답변 생성
            if docs:
                context = "\n\n".join([doc.page_content[:300] for doc in docs])
                prompt = f"컨텍스트: {context}\n\n질문: {question}\n\n답변:"
                response = llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                answer = "관련 문서를 찾을 수 없습니다."

            elapsed_time = time.time() - start_time

            print(f"  답변: {answer[:100]}...")
            print(f"  응답 시간: {elapsed_time:.2f}초")
            print(f"  검색된 문서: {len(docs)}개")

    elif args.mode == 'web':
        # 웹 UI 모드
        print("Streamlit 웹 UI를 시작합니다...")
        print("브라우저에서 http://localhost:8501 로 접속하세요.")
        print("\n종료하려면 Ctrl+C를 누르세요.")

        import subprocess
        subprocess.run(["streamlit", "run", "demo.py"])

    print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()