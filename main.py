"""
LangChain 문서 챗봇 메인 통합 모듈
모든 컴포넌트를 통합하여 완전한 RAG 시스템을 구성
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# 모듈 임포트
from llm import get_llm, get_embeddings, test_connection
from vector_database import VectorDatabase
from data_collector import LangChainDataCollector
from retriever import HybridRetriever
from conversation import ConversationManager
from text_to_sql import TextToSQLRAG
from evaluator import RAGEvaluator
from prompts import get_system_prompt, format_context


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LangChainRAGChatbot:
    """통합 RAG 챗봇 시스템"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        챗봇 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config or self._get_default_config()
        self.components_initialized = False

        # 컴포넌트 초기화
        self._initialize_components()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'chroma_path': './data/chroma_db',
            'db_path': './data/langchain.db',
            'model_name': 'solar-1-mini-chat',
            'temperature': 0.7,
            'max_tokens': 1000,
            'memory_type': 'buffer_window',
            'window_size': 10,
            'search_mode': 'hybrid',
            'top_k': 5
        }

    def _initialize_components(self):
        """모든 컴포넌트 초기화"""
        try:
            logger.info("컴포넌트 초기화 시작...")

            # 1. LLM 및 임베딩 초기화
            logger.info("LLM 및 임베딩 초기화...")
            self.llm = get_llm(
                model_name=self.config['model_name'],
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens']
            )
            self.embeddings = get_embeddings()

            # 2. 벡터 데이터베이스 초기화
            logger.info("벡터 데이터베이스 초기화...")
            self.vector_db = VectorDatabase(
                persist_directory=self.config['chroma_path'],
                embedding_function=self.embeddings
            )

            # 3. Retriever 초기화
            logger.info("Retriever 초기화...")
            self.retriever = HybridRetriever(
                vector_db=self.vector_db,
                db_path=self.config['db_path']
            )

            # 4. 대화 매니저 초기화
            logger.info("대화 매니저 초기화...")
            self.conversation = ConversationManager(
                llm=self.llm,
                memory_type=self.config['memory_type'],
                window_size=self.config['window_size']
            )

            # 5. Text-to-SQL RAG 초기화
            logger.info("Text-to-SQL RAG 초기화...")
            self.text_to_sql = TextToSQLRAG(
                db_path=self.config['db_path']
            )

            # 6. 평가기 초기화
            logger.info("평가기 초기화...")
            self.evaluator = RAGEvaluator(
                retriever=self.retriever,
                db_path=self.config['db_path']
            )

            # 7. 데이터 수집기 초기화
            logger.info("데이터 수집기 초기화...")
            self.collector = LangChainDataCollector(
                db_path=self.config['db_path']
            )

            self.components_initialized = True
            logger.info("모든 컴포넌트 초기화 완료!")

        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {str(e)}")
            self.components_initialized = False
            raise

    def chat(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        use_sql: bool = False,
        evaluate: bool = False
    ) -> Dict[str, Any]:
        """
        사용자 질문에 대한 응답 생성

        Args:
            question: 사용자 질문
            conversation_id: 대화 ID
            use_sql: SQL 모드 사용 여부
            evaluate: 평가 수행 여부

        Returns:
            응답 딕셔너리
        """
        if not self.components_initialized:
            return {
                'error': '컴포넌트가 초기화되지 않았습니다.',
                'answer': None
            }

        try:
            # SQL 모드 처리
            if use_sql:
                return self._handle_sql_query(question)

            # RAG 처리
            response = self._handle_rag_query(question, conversation_id)

            # 평가 수행
            if evaluate:
                eval_result = self.evaluator.run_full_evaluation(
                    question=question,
                    generated_answer=response['answer']
                )
                response['evaluation'] = {
                    'overall_score': eval_result.overall_score,
                    'relevance_score': eval_result.relevance_score,
                    'accuracy_score': eval_result.accuracy_score,
                    'completeness_score': eval_result.completeness_score
                }

            return response

        except Exception as e:
            logger.error(f"챗봇 처리 중 오류 발생: {str(e)}")
            return {
                'error': str(e),
                'answer': None
            }

    def _handle_rag_query(
        self,
        question: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """RAG 쿼리 처리"""
        # 1. 문서 검색
        search_mode = self.config['search_mode']
        top_k = self.config['top_k']

        if search_mode == 'hybrid':
            retrieved_docs = self.retriever.hybrid_search(question, top_k=top_k)
        elif search_mode == 'vector':
            retrieved_docs = self.retriever.vector_search(question, top_k=top_k)
        else:
            retrieved_docs = self.retriever.sql_search(question, limit=top_k)

        # 2. 컨텍스트 생성
        context = format_context(retrieved_docs[:3])

        # 3. 시스템 프롬프트 가져오기
        system_prompt = get_system_prompt()

        # 4. 대화 컨텍스트 추가 (대화 ID가 있을 경우)
        if conversation_id:
            # 대화 기록 가져오기
            messages = self.conversation.get_conversation_messages(conversation_id)
            conversation_context = self._format_conversation_history(messages[-4:])  # 최근 4개
        else:
            conversation_context = ""

        # 5. 최종 프롬프트 구성
        full_prompt = f"""
        {system_prompt}

        {conversation_context}

        현재 질문: {question}

        관련 문서:
        {context}

        위 정보를 바탕으로 질문에 답변해주세요.
        """

        # 6. LLM 응답 생성
        response = self.llm.invoke(full_prompt)
        answer = response.content

        # 7. 대화 저장 (대화 ID가 있을 경우)
        if conversation_id:
            self.conversation.add_message(conversation_id, 'user', question)
            self.conversation.add_message(conversation_id, 'assistant', answer)

        return {
            'answer': answer,
            'sources': [
                {
                    'title': doc.metadata.get('title', 'Unknown'),
                    'url': doc.metadata.get('url', ''),
                    'content': doc.page_content[:200]
                }
                for doc in retrieved_docs[:3]
            ],
            'num_sources': len(retrieved_docs)
        }

    def _handle_sql_query(self, question: str) -> Dict[str, Any]:
        """SQL 쿼리 처리"""
        result = self.text_to_sql.text_to_sql_rag(
            question=question,
            return_documents=True
        )

        return {
            'answer': result['formatted_results'],
            'sql_query': result['sql_query'],
            'sources': [
                {
                    'title': 'SQL Query Result',
                    'content': result['formatted_results']
                }
            ] if result['documents'] else [],
            'error': result.get('error')
        }

    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """대화 기록 포맷팅"""
        if not messages:
            return ""

        history = "이전 대화:\n"
        for msg in messages:
            role = "사용자" if msg['role'] == 'user' else "어시스턴트"
            history += f"{role}: {msg['content']}\n"

        return history

    def collect_documents(self, urls: List[str]) -> Dict[str, Any]:
        """문서 수집 및 저장"""
        results = {
            'total_documents': 0,
            'successful_urls': [],
            'failed_urls': [],
            'errors': []
        }

        for url in urls:
            try:
                logger.info(f"수집 중: {url}")

                # 문서 수집
                documents = self.collector.collect_from_url(url)

                if documents:
                    # 벡터 DB에 추가
                    self.vector_db.add_documents(documents)

                    # SQLite에 저장
                    self.collector.save_to_database(documents)

                    results['total_documents'] += len(documents)
                    results['successful_urls'].append(url)
                    logger.info(f"수집 완료: {url} ({len(documents)}개 문서)")
                else:
                    results['failed_urls'].append(url)
                    logger.warning(f"문서를 찾을 수 없음: {url}")

            except Exception as e:
                logger.error(f"문서 수집 실패: {url} - {str(e)}")
                results['failed_urls'].append(url)
                results['errors'].append({
                    'url': url,
                    'error': str(e)
                })

        return results

    def create_new_conversation(self) -> str:
        """새 대화 생성"""
        return self.conversation.create_conversation()

    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """대화 기록 조회"""
        return self.conversation.get_conversation_history(limit=limit)

    def evaluate_system(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """시스템 평가 실행"""
        return self.evaluator.batch_evaluate(test_cases, save_report=True)

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 반환"""
        return {
            'vector_db_count': self.vector_db.get_collection_stats().get('count', 0),
            'conversation_count': len(self.get_conversation_history(100)),
            'memory_type': self.config['memory_type'],
            'model_name': self.config['model_name'],
            'search_mode': self.config['search_mode']
        }


def run_cli():
    """CLI 인터페이스 실행"""
    parser = argparse.ArgumentParser(description='LangChain RAG 챗봇 CLI')

    parser.add_argument('--mode', choices=['chat', 'collect', 'evaluate', 'demo'],
                        default='chat', help='실행 모드')
    parser.add_argument('--question', type=str, help='질문 (chat 모드)')
    parser.add_argument('--urls', nargs='+', help='수집할 URL 목록 (collect 모드)')
    parser.add_argument('--sql', action='store_true', help='SQL 모드 사용')
    parser.add_argument('--evaluate', action='store_true', help='평가 수행')

    args = parser.parse_args()

    # 챗봇 초기화
    chatbot = LangChainRAGChatbot()

    if args.mode == 'chat':
        if args.question:
            # 단일 질문 처리
            result = chatbot.chat(
                args.question,
                use_sql=args.sql,
                evaluate=args.evaluate
            )
            print(f"\n질문: {args.question}")
            print(f"답변: {result.get('answer', 'N/A')}")

            if result.get('sources'):
                print("\n참고 문서:")
                for source in result['sources']:
                    print(f"  - {source['title']}")

            if result.get('evaluation'):
                print(f"\n평가 점수: {result['evaluation']['overall_score']:.2f}")
        else:
            # 대화형 모드
            print("환영합니다! LangChain RAG 챗봇 (종료: 'exit' 또는 'quit')")
            print("-" * 50)

            conversation_id = chatbot.create_new_conversation()
            print(f"새 대화 시작 (ID: {conversation_id})\n")

            while True:
                question = input("질문을 입력하세요: ").strip()

                if question.lower() in ['exit', 'quit']:
                    print("챗봇을 종료합니다.")
                    break

                if not question:
                    continue

                result = chatbot.chat(
                    question,
                    conversation_id=conversation_id,
                    use_sql=args.sql
                )

                print(f"\n답변: {result.get('answer', 'N/A')}\n")
                print("-" * 50)

    elif args.mode == 'collect':
        if args.urls:
            print("문서 수집을 시작합니다...")
            results = chatbot.collect_documents(args.urls)

            print(f"\n수집 완료:")
            print(f"  - 총 문서: {results['total_documents']}개")
            print(f"  - 성공 URL: {len(results['successful_urls'])}개")
            print(f"  - 실패 URL: {len(results['failed_urls'])}개")
        else:
            print("수집할 URL을 지정해주세요. (--urls URL1 URL2 ...)")

    elif args.mode == 'evaluate':
        print("시스템 평가를 시작합니다...")

        # 테스트 케이스 생성
        test_cases = [
            {'question': "LangChain이란 무엇인가요?"},
            {'question': "벡터 데이터베이스는 어떻게 사용하나요?"},
            {'question': "프롬프트를 어떻게 작성하나요?"}
        ]

        results = chatbot.evaluate_system(test_cases)

        print(f"\n평가 완료:")
        print(f"  - 평가 점수: {results['avg_overall_score']:.2f}")
        print(f"  - 평균 응답 시간: {results['avg_response_time']:.2f}초")

    elif args.mode == 'demo':
        print("Streamlit 데모를 시작합니다...")
        os.system("streamlit run demo.py")


def run_web():
    """Streamlit 웹 인터페이스 실행"""
    import subprocess
    subprocess.run(["streamlit", "run", "demo.py"])


# 메인 실행
if __name__ == "__main__":
    # 인수가 없으면 웹 인터페이스, 있으면 CLI
    if len(sys.argv) == 1:
        print("웹 인터페이스를 시작합니다...")
        run_web()
    else:
        run_cli()
