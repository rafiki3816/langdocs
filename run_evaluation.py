#!/usr/bin/env python3
"""
성능 평가 스크립트
"""

import sys
import os
import time
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import get_llm
from retriever import HybridRetriever
from evaluator import RAGEvaluator

def run_evaluation():
    """평가 실행"""

    print("="*60)
    print("🎯 LangChain RAG 시스템 성능 평가")
    print("="*60)

    # 시스템 초기화
    print("\n📋 초기화 중...")
    llm = get_llm(model="solar-pro", temperature=0.3)
    retriever = HybridRetriever()
    evaluator = RAGEvaluator()  # RAGEvaluator는 매개변수 없이 초기화

    # 평가용 테스트 케이스
    test_cases = [
        {
            "question": "LangChain이란 무엇인가요?",
            "expected_keywords": ["프레임워크", "LLM", "애플리케이션"],
            "category": "기초"
        },
        {
            "question": "RAG 시스템의 구성 요소는?",
            "expected_keywords": ["검색", "생성", "임베딩", "벡터"],
            "category": "중급"
        },
        {
            "question": "Agent의 역할은?",
            "expected_keywords": ["의사결정", "도구", "실행", "계획"],
            "category": "중급"
        },
        {
            "question": "ConversationBufferMemory와 ConversationSummaryMemory의 차이점은?",
            "expected_keywords": ["전체 저장", "요약", "토큰", "메모리"],
            "category": "고급"
        },
        {
            "question": "LCEL의 장점은?",
            "expected_keywords": ["체인", "구성", "파이프", "선언적"],
            "category": "고급"
        }
    ]

    print(f"📝 {len(test_cases)}개 케이스 평가 시작\n")

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test_case['category']}: {test_case['question'][:30]}...")

        start_time = time.time()

        # 문서 검색
        search_results = retriever.hybrid_search(test_case["question"], k=5)
        docs = [result.document for result in search_results] if search_results else []

        # 컨텍스트 생성
        context = "\n".join([doc.page_content[:500] for doc in docs]) if docs else ""

        # 답변 생성
        prompt = f"""컨텍스트: {context}
질문: {test_case['question']}
답변:"""

        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)

        response_time = time.time() - start_time

        # 평가 메트릭 계산
        keyword_matches = sum(1 for keyword in test_case["expected_keywords"]
                            if keyword.lower() in answer.lower())
        keyword_coverage = keyword_matches / len(test_case["expected_keywords"])

        # 결과 저장
        result = {
            "question": test_case["question"],
            "category": test_case["category"],
            "answer_length": len(answer),
            "response_time": response_time,
            "num_docs": len(docs),
            "keyword_coverage": keyword_coverage,
            "keyword_matches": f"{keyword_matches}/{len(test_case['expected_keywords'])}"
        }
        results.append(result)

        print(f"  ⏱️ 시간: {response_time:.2f}초")
        print(f"  📊 키워드 매칭: {result['keyword_matches']}")
        print(f"  📈 커버리지: {keyword_coverage:.0%}\n")

    # 전체 통계 계산
    print("="*60)
    print("📊 평가 결과 요약")
    print("="*60)

    avg_time = sum(r["response_time"] for r in results) / len(results)
    avg_coverage = sum(r["keyword_coverage"] for r in results) / len(results)
    avg_docs = sum(r["num_docs"] for r in results) / len(results)
    avg_length = sum(r["answer_length"] for r in results) / len(results)

    print(f"\n✅ 평균 응답 시간: {avg_time:.2f}초")
    print(f"✅ 평균 키워드 커버리지: {avg_coverage:.0%}")
    print(f"✅ 평균 참조 문서 수: {avg_docs:.1f}개")
    print(f"✅ 평균 답변 길이: {avg_length:.0f}자")

    # 카테고리별 분석
    print("\n📈 카테고리별 성능:")
    for category in ["기초", "중급", "고급"]:
        cat_results = [r for r in results if r["category"] == category]
        if cat_results:
            cat_coverage = sum(r["keyword_coverage"] for r in cat_results) / len(cat_results)
            cat_time = sum(r["response_time"] for r in cat_results) / len(cat_results)
            print(f"  {category}: 커버리지 {cat_coverage:.0%}, 응답시간 {cat_time:.2f}초")

    # 성능 등급 판정
    print("\n🏆 시스템 성능 등급:")
    if avg_coverage >= 0.8 and avg_time <= 5:
        grade = "A (우수)"
    elif avg_coverage >= 0.6 and avg_time <= 7:
        grade = "B (양호)"
    elif avg_coverage >= 0.4:
        grade = "C (보통)"
    else:
        grade = "D (개선 필요)"

    print(f"  등급: {grade}")

    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"evaluation_report_{timestamp}.json"

    report = {
        "timestamp": timestamp,
        "test_cases": len(test_cases),
        "average_metrics": {
            "response_time": avg_time,
            "keyword_coverage": avg_coverage,
            "num_docs": avg_docs,
            "answer_length": avg_length
        },
        "grade": grade,
        "detailed_results": results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 평가 보고서 저장: {report_file}")

    # 개선 제안
    print("\n💡 개선 제안:")
    if avg_time > 5:
        print("  - 응답 시간이 길어 캐싱 또는 최적화 필요")
    if avg_coverage < 0.7:
        print("  - 키워드 커버리지가 낮아 문서 품질 개선 필요")
    if avg_docs < 3:
        print("  - 참조 문서가 적어 더 많은 문서 수집 필요")

    return report

if __name__ == "__main__":
    run_evaluation()