#!/usr/bin/env python3
"""
챗봇 테스트 스크립트
LangChain 질문으로 챗봇의 성능을 테스트
"""

import sys
import os
import time
from datetime import datetime
import json

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import get_llm, get_embeddings
from retriever import HybridRetriever
from conversation import ConversationManager


def test_chatbot():
    """챗봇 테스트 실행"""

    print("="*60)
    print("🧪 LangChain 챗봇 테스트 시작")
    print("="*60)

    # 시스템 초기화
    print("\n📋 시스템 초기화 중...")
    llm = get_llm(model="solar-pro", temperature=0.7)
    embeddings = get_embeddings(model="solar-embedding-1-large")
    retriever = HybridRetriever()
    conversation_manager = ConversationManager()

    print("✅ 시스템 초기화 완료\n")

    # 테스트 질문들
    test_questions = [
        # 기초 질문
        {
            "category": "기초",
            "questions": [
                "LangChain이란 무엇인가요?",
                "그것의 주요 구성 요소를 설명해주세요",
                "Prompt Template은 왜 필요한가요?"
            ]
        },
        # 중급 질문
        {
            "category": "중급",
            "questions": [
                "RAG 시스템의 작동 원리를 설명해주세요",
                "Agent와 Tool의 관계는 무엇인가요?"
            ]
        },
        # 고급 질문
        {
            "category": "고급",
            "questions": [
                "Hybrid Search를 구현하는 방법은?",
                "Production 환경 최적화 방법은?"
            ]
        }
    ]

    results = []
    total_questions = sum(len(cat["questions"]) for cat in test_questions)
    question_num = 0

    print(f"📝 총 {total_questions}개 질문 테스트\n")

    for category_data in test_questions:
        category = category_data["category"]
        print(f"\n{'='*40}")
        print(f"📚 {category} 질문 테스트")
        print(f"{'='*40}")

        for question in category_data["questions"]:
            question_num += 1
            print(f"\n[{question_num}/{total_questions}] 질문: {question}")

            start_time = time.time()

            try:
                # 문서 검색 (hybrid_search 사용)
                search_results = retriever.hybrid_search(question, k=5)
                docs = [result.document for result in search_results] if search_results else []

                # 컨텍스트 생성
                context = ""
                sources = []
                if docs:
                    context = "\n\n".join([doc.page_content[:300] for doc in docs])
                    sources = [doc.metadata.get('title', 'Unknown') for doc in docs[:3]]

                # 프롬프트 생성
                prompt = f"""당신은 LangChain 전문가입니다.
아래 컨텍스트를 참고하여 질문에 답변해주세요.

컨텍스트:
{context}

질문: {question}

답변:"""

                # 응답 생성
                response = llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)

                response_time = time.time() - start_time

                # 답변 길이 제한하여 출력
                display_answer = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"✅ 답변: {display_answer}")
                print(f"⏱️ 응답 시간: {response_time:.2f}초")
                print(f"📚 참고 문서: {len(docs)}개")

                # 결과 저장
                results.append({
                    "category": category,
                    "question": question,
                    "answer_length": len(answer),
                    "response_time": response_time,
                    "num_docs": len(docs),
                    "sources": sources[:3],
                    "success": True
                })

                # 대화 관리자에 저장
                conversation_manager.add_user_message(question)
                conversation_manager.add_assistant_message(answer)

            except Exception as e:
                print(f"❌ 오류: {str(e)}")
                results.append({
                    "category": category,
                    "question": question,
                    "success": False,
                    "error": str(e)
                })

    # 테스트 결과 분석
    print("\n" + "="*60)
    print("📊 테스트 결과 분석")
    print("="*60)

    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]

    if successful_tests:
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        avg_answer_length = sum(r["answer_length"] for r in successful_tests) / len(successful_tests)
        avg_docs = sum(r["num_docs"] for r in successful_tests) / len(successful_tests)

        print(f"\n✅ 성공: {len(successful_tests)}/{total_questions}")
        print(f"❌ 실패: {len(failed_tests)}/{total_questions}")
        print(f"\n📈 평균 통계:")
        print(f"  - 응답 시간: {avg_response_time:.2f}초")
        print(f"  - 답변 길이: {avg_answer_length:.0f}자")
        print(f"  - 참조 문서: {avg_docs:.1f}개")

        # 카테고리별 분석
        print(f"\n📊 카테고리별 성공률:")
        for cat_name in ["기초", "중급", "고급"]:
            cat_results = [r for r in successful_tests if r["category"] == cat_name]
            total_cat = len([q for cat in test_questions if cat["category"] == cat_name for q in cat["questions"]])
            success_rate = (len(cat_results) / total_cat * 100) if total_cat > 0 else 0
            print(f"  - {cat_name}: {success_rate:.0f}% ({len(cat_results)}/{total_cat})")

    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.json"

    report = {
        "timestamp": timestamp,
        "total_questions": total_questions,
        "successful": len(successful_tests),
        "failed": len(failed_tests),
        "results": results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 상세 결과 저장: {report_file}")

    return results


if __name__ == "__main__":
    test_chatbot()