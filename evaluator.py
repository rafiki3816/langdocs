"""평가 시스템 모듈
RAG 시스템 성능 평가 및 메트릭 측정"""

import json
import time
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from langchain.evaluation import load_evaluator
from langchain.evaluation.qa import QAEvalChain
from langchain.prompts import PromptTemplate

from llm import get_llm, get_embeddings
from retriever import HybridRetriever
from prompts import get_evaluation_template


@dataclass
class EvaluationResult:
    """평가 결과를 저장하는 데이터 클래스"""
    question: str
    generated_answer: str
    reference_answer: Optional[str]
    relevance_score: float
    accuracy_score: float
    completeness_score: float
    response_time: float
    retrieval_precision: float
    retrieval_recall: float
    overall_score: float
    metadata: Dict[str, Any]


class RAGEvaluator:
    """RAG 시스템 평가자 클래스"""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        db_path: str = "./data/langchain.db"
    ):
        """
        RAGEvaluator 초기화

        Args:
            retriever: 검색기 (retriever) 인스턴스
            db_path: SQLite 데이터베이스 경로
        """
        self.retriever = retriever or HybridRetriever()
        self.llm = get_llm()
        self.embeddings = get_embeddings()
        self.db_path = db_path

        # 평가 결과 저장을 위한 테이블 생성
        self._init_evaluation_db()

    def _init_evaluation_db(self):
        """평가 결과 저장을 위한 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                generated_answer TEXT,
                reference_answer TEXT,
                relevance_score REAL,
                accuracy_score REAL,
                completeness_score REAL,
                response_time REAL,
                retrieval_precision REAL,
                retrieval_recall REAL,
                overall_score REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def evaluate_answer_quality(
        self,
        question: str,
        generated_answer: str,
        reference_answer: Optional[str] = None
    ) -> Dict[str, float]:
        """
        생성된 답변의 품질 평가

        Args:
            question: 질문
            generated_answer: 생성된 답변
            reference_answer: 참조 답변 (선택)

        Returns:
            평가 점수 딕셔너리
        """
        scores = {}

        # 1. 관련성 평가 (Relevance)
        relevance_prompt = f"""
질문과 답변의 관련성을 0에서 1 사이의 숫자로 평가해주세요.

질문: {question}
답변: {generated_answer}

평가 기준:
- 답변이 질문과 직접적으로 관련이 있는가?
- 질문에서 요구하는 정보를 제공하는가?

숫자만 반환하세요 (예: 0.85):
"""

        relevance_score = self._get_llm_score(relevance_prompt)
        scores['relevance'] = relevance_score

        # 2. 정확성 평가 (Accuracy)
        if reference_answer:
            # 참조 답변이 있을 경우 비교
            accuracy_prompt = f"""
생성된 답변의 정확성을 참조 답변과 비교하여 0에서 1 사이의 숫자로 평가해주세요.

질문: {question}
생성된 답변: {generated_answer}
참조 답변: {reference_answer}

평가 기준:
- 핵심 내용이 일치하는가?
- 사실 관계가 정확한가?

숫자만 반환하세요 (예: 0.75):
"""
            accuracy_score = self._get_llm_score(accuracy_prompt)
        else:
            # 참조 답변이 없을 경우 일반적 평가
            accuracy_prompt = f"""
답변의 정확성을 0에서 1 사이의 숫자로 평가해주세요.

질문: {question}
답변: {generated_answer}

평가 기준:
- LangChain 관련 내용이 정확한가?
- 오류나 잘못된 정보가 없는가?

숫자만 반환하세요 (예: 0.80):
"""
            accuracy_score = self._get_llm_score(accuracy_prompt)

        scores['accuracy'] = accuracy_score

        # 3. 완전성 평가 (Completeness)
        completeness_prompt = f"""
답변의 완전성을 0에서 1 사이의 숫자로 평가해주세요.

질문: {question}
답변: {generated_answer}

평가 기준:
- 질문에서 요구하는 모든 정보를 제공하는가?
- 충분히 상세한가?
- 예제나 추가 설명이 적절히 포함되어 있는가?

숫자만 반환하세요 (예: 0.70):
"""

        completeness_score = self._get_llm_score(completeness_prompt)
        scores['completeness'] = completeness_score

        return scores

    def evaluate_retrieval_performance(
        self,
        question: str,
        retrieved_docs: List[Any],
        relevant_doc_ids: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        검색 성능 평가

        Args:
            question: 질문
            retrieved_docs: 검색된 문서 리스트
            relevant_doc_ids: 관련 문서 ID 리스트 (선택)

        Returns:
            검색 성능 메트릭 딕셔너리
        """
        metrics = {}

        if not retrieved_docs:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'mrr': 0.0  # Mean Reciprocal Rank
            }

        # 검색된 문서의 ID 추출
        retrieved_ids = []
        for doc in retrieved_docs:
            if hasattr(doc, 'metadata') and 'id' in doc.metadata:
                retrieved_ids.append(doc.metadata['id'])

        if relevant_doc_ids:
            # Precision: 검색된 문서 중 관련 문서의 비율
            relevant_retrieved = set(retrieved_ids) & set(relevant_doc_ids)
            precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0
            metrics['precision'] = precision

            # Recall: 관련 문서 중 검색된 문서의 비율
            recall = len(relevant_retrieved) / len(relevant_doc_ids) if relevant_doc_ids else 0
            metrics['recall'] = recall

            # F1 Score
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0
            metrics['f1_score'] = f1

            # MRR (Mean Reciprocal Rank)
            mrr = 0
            for i, doc_id in enumerate(retrieved_ids):
                if doc_id in relevant_doc_ids:
                    mrr = 1 / (i + 1)
                    break
            metrics['mrr'] = mrr
        else:
            # 관련 문서 ID가 없을 경우 LLM으로 평가
            relevance_scores = []
            for doc in retrieved_docs[:5]:  # 최대 5개만 평가
                prompt = f"""
질문과 문서의 관련성을 0에서 1 사이의 숫자로 평가해주세요.

질문: {question}
문서: {doc.page_content[:500]}

숫자만 반환하세요:
"""
                score = self._get_llm_score(prompt)
                relevance_scores.append(score)

            avg_relevance = np.mean(relevance_scores) if relevance_scores else 0
            metrics['precision'] = avg_relevance
            metrics['recall'] = avg_relevance  # 근사값
            metrics['f1_score'] = avg_relevance
            metrics['mrr'] = relevance_scores[0] if relevance_scores else 0

        return metrics

    def evaluate_response_time(
        self,
        question: str,
        include_retrieval: bool = True,
        include_generation: bool = True
    ) -> Dict[str, float]:
        """
        응답 시간 측정

        Args:
            question: 질문
            include_retrieval: 검색 시간 포함 여부
            include_generation: 생성 시간 포함 여부

        Returns:
            시간 측정 결과 딕셔너리
        """
        times = {}

        # 검색 시간 측정
        if include_retrieval:
            start = time.time()
            docs = self.retriever.hybrid_search(question)
            retrieval_time = time.time() - start
            times['retrieval_time'] = retrieval_time
        else:
            docs = []

        # 생성 시간 측정
        if include_generation:
            context = "\n".join([doc.page_content for doc in docs[:3]])
            prompt = f"""
다음 컨텍스트를 참고하여 질문에 답변해주세요.

컨텍스트: {context}
질문: {question}

답변:
"""

            start = time.time()
            response = self.llm.invoke(prompt)
            generation_time = time.time() - start
            times['generation_time'] = generation_time

        # 총 응답 시간
        times['total_time'] = sum(times.values())

        return times

    def _get_llm_score(self, prompt: str) -> float:
        """LLM을 사용하여 점수를 얻음"""
        try:
            response = self.llm.invoke(prompt)
            score_text = response.content.strip()

            # 숫자 추출
            import re
            match = re.search(r'(0?\.\d+|1\.0|0|1)', score_text)
            if match:
                return float(match.group(1))
            return 0.5  # 기본값
        except Exception as e:
            print(f"점수 추출 실패: {e}")
            return 0.5

    def run_full_evaluation(
        self,
        question: str,
        generated_answer: str,
        reference_answer: Optional[str] = None,
        relevant_doc_ids: Optional[List[int]] = None
    ) -> EvaluationResult:
        """
        전체 평가 실행

        Args:
            question: 질문
            generated_answer: 생성된 답변
            reference_answer: 참조 답변 (선택)
            relevant_doc_ids: 관련 문서 ID 리스트 (선택)

        Returns:
            종합 평가 결과
        """
        # 응답 시간 측정
        time_metrics = self.evaluate_response_time(question)

        # 검색 성능 평가
        retrieved_docs = self.retriever.hybrid_search(question)
        retrieval_metrics = self.evaluate_retrieval_performance(
            question, retrieved_docs, relevant_doc_ids
        )

        # 답변 품질 평가
        quality_scores = self.evaluate_answer_quality(
            question, generated_answer, reference_answer
        )

        # 종합 점수 계산 (가중 평균)
        overall_score = (
            quality_scores['relevance'] * 0.3 +
            quality_scores['accuracy'] * 0.3 +
            quality_scores['completeness'] * 0.2 +
            retrieval_metrics['precision'] * 0.1 +
            retrieval_metrics['recall'] * 0.1
        )

        # 결과 객체 생성
        result = EvaluationResult(
            question=question,
            generated_answer=generated_answer,
            reference_answer=reference_answer,
            relevance_score=quality_scores['relevance'],
            accuracy_score=quality_scores['accuracy'],
            completeness_score=quality_scores['completeness'],
            response_time=time_metrics['total_time'],
            retrieval_precision=retrieval_metrics['precision'],
            retrieval_recall=retrieval_metrics['recall'],
            overall_score=overall_score,
            metadata={
                'time_metrics': time_metrics,
                'retrieval_metrics': retrieval_metrics,
                'quality_scores': quality_scores,
                'num_retrieved_docs': len(retrieved_docs)
            }
        )

        # 결과 저장
        self.save_evaluation_result(result)

        return result

    def save_evaluation_result(self, result: EvaluationResult):
        """평가 결과를 데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO evaluations (
                question, generated_answer, reference_answer,
                relevance_score, accuracy_score, completeness_score,
                response_time, retrieval_precision, retrieval_recall,
                overall_score, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.question,
            result.generated_answer,
            result.reference_answer,
            result.relevance_score,
            result.accuracy_score,
            result.completeness_score,
            result.response_time,
            result.retrieval_precision,
            result.retrieval_recall,
            result.overall_score,
            json.dumps(result.metadata)
        ))

        conn.commit()
        conn.close()

    def batch_evaluate(
        self,
        test_cases: List[Dict[str, Any]],
        save_report: bool = True
    ) -> Dict[str, Any]:
        """
        배치 평가 실행

        Args:
            test_cases: 테스트 케이스 리스트
            save_report: 보고서 저장 여부

        Returns:
            평가 통계 딕셔너리
        """
        results = []

        for test_case in test_cases:
            print(f"평가 중: {test_case['question'][:50]}...")

            # RAG 시스템으로 답변 생성
            retrieved_docs = self.retriever.hybrid_search(test_case['question'])
            context = "\n".join([doc.page_content for doc in retrieved_docs[:3]])

            prompt = f"""
다음 컨텍스트를 참고하여 질문에 답변해주세요.

컨텍스트: {context}
질문: {test_case['question']}

답변:
"""

            response = self.llm.invoke(prompt)
            generated_answer = response.content

            # 평가 실행
            result = self.run_full_evaluation(
                question=test_case['question'],
                generated_answer=generated_answer,
                reference_answer=test_case.get('reference_answer'),
                relevant_doc_ids=test_case.get('relevant_doc_ids')
            )

            results.append(result)

        # 통계 계산
        statistics = self._calculate_statistics(results)

        # 보고서 저장
        if save_report:
            self._save_evaluation_report(results, statistics)

        return statistics

    def _calculate_statistics(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """평가 결과 통계 계산"""
        if not results:
            return {}

        stats = {
            'num_evaluations': len(results),
            'avg_relevance_score': np.mean([r.relevance_score for r in results]),
            'avg_accuracy_score': np.mean([r.accuracy_score for r in results]),
            'avg_completeness_score': np.mean([r.completeness_score for r in results]),
            'avg_response_time': np.mean([r.response_time for r in results]),
            'avg_retrieval_precision': np.mean([r.retrieval_precision for r in results]),
            'avg_retrieval_recall': np.mean([r.retrieval_recall for r in results]),
            'avg_overall_score': np.mean([r.overall_score for r in results]),
            'std_overall_score': np.std([r.overall_score for r in results]),
            'min_overall_score': min([r.overall_score for r in results]),
            'max_overall_score': max([r.overall_score for r in results])
        }

        return stats

    def _save_evaluation_report(
        self,
        results: List[EvaluationResult],
        statistics: Dict[str, Any]
    ):
        """평가 보고서 저장"""
        report = {
            'evaluation_date': datetime.now().isoformat(),
            'statistics': statistics,
            'detailed_results': [asdict(r) for r in results]
        }

        # JSON 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./data/evaluation_report_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"평가 보고서 저장됨: {filename}")

    def get_evaluation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """평가 기록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM evaluations
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            if result['metadata']:
                result['metadata'] = json.loads(result['metadata'])
            results.append(result)

        conn.close()
        return results


def create_test_cases() -> List[Dict[str, Any]]:
    """평가용 테스트 케이스 생성"""
    test_cases = [
        {
            'question': "LangChain이 무엇인가요?",
            'reference_answer': "LangChain은 대규모 언어 모델(LLM)을 활용한 애플리케이션을 구축하기 위한 프레임워크입니다."
        },
        {
            'question': "LangChain에서 체인(Chain)은 무엇이며 어떻게 사용하나요?",
            'reference_answer': "LangChain에서 체인은 여러 컴포넌트를 연결하여 복잡한 작업을 수행하는 구조입니다."
        },
        {
            'question': "벡터 스토어는 어떻게 사용하나요?",
            'reference_answer': "벡터 스토어는 임베딩된 문서를 저장하고 유사도 검색을 수행하는 역할을 합니다."
        },
        {
            'question': "RAG 시스템의 구성 요소는?",
            'reference_answer': "RAG 시스템은 검색기(Retriever)와 생성기(Generator)로 구성됩니다."
        },
        {
            'question': "프롬프트 템플릿을 사용하는 이유는?",
            'reference_answer': "프롬프트 템플릿은 재사용 가능한 프롬프트를 생성하고 일관성을 유지하기 위해 사용됩니다."
        }
    ]

    return test_cases


# 메인 실행
if __name__ == "__main__":
    print("=" * 50)
    print("RAG 평가 시스템 테스트\n")

    # 평가자 초기화
    evaluator = RAGEvaluator()

    # 1. 단일 평가 테스트
    print("1. 단일 평가 테스트")
    test_question = "LangChain에서 메모리를 어떻게 사용하나요?"
    test_answer = """
LangChain에서 메모리를 사용하는 방법은 다양합니다:

1. ConversationBufferMemory: 모든 대화 내역 저장
2. ConversationSummaryMemory: 대화 요약본 저장
3. ConversationBufferWindowMemory: 최근 N개의 대화만 저장

예시:
```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory()
```
"""

    result = evaluator.run_full_evaluation(
        question=test_question,
        generated_answer=test_answer
    )

    print(f"질문: {test_question}")
    print(f"관련성: {result.relevance_score:.2f}")
    print(f"정확성: {result.accuracy_score:.2f}")
    print(f"완전성: {result.completeness_score:.2f}")
    print(f"종합 점수: {result.overall_score:.2f}")
    print(f"응답 시간: {result.response_time:.2f}초")

    # 2. 배치 평가 테스트
    print("\n2. 배치 평가 테스트")
    test_cases = create_test_cases()
    statistics = evaluator.batch_evaluate(test_cases[:3])  # 처음 3개만 테스트

    print("\n=== 평가 통계 ===")
    print(f"평가 수: {statistics['num_evaluations']}")
    print(f"평균 종합 점수: {statistics['avg_overall_score']:.2f}")
    print(f"평균 응답 시간: {statistics['avg_response_time']:.2f}초")
    print(f"최고 점수: {statistics['max_overall_score']:.2f}")
    print(f"최저 점수: {statistics['min_overall_score']:.2f}")

    # 3. 평가 기록 조회
    print("\n3. 최근 평가 기록 조회")
    history = evaluator.get_evaluation_history(limit=5)
    for i, record in enumerate(history[:3], 1):
        print(f"\n[{i}] {record['question'][:50]}...")
        print(f"    종합 점수: {record['overall_score']:.2f}")
        print(f"    생성 시간: {record['created_at']}")

    print("\n평가 시스템 테스트 완료!")
