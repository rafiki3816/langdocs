#!/usr/bin/env python3
"""
대화 메모리가 있는 CLI 챗봇
연속 질문을 처리할 수 있는 터미널 버전
"""

import sys
import os
from typing import List, Dict
from datetime import datetime
from colorama import init, Fore, Style

# colorama 초기화
init()

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import get_llm, get_embeddings
from vector_database import VectorDatabase
from retriever import HybridRetriever
from conversation import ConversationManager


class MemoryChatbot:
    """대화 메모리가 있는 챗봇"""

    def __init__(self):
        print(f"{Fore.CYAN}🤖 LangChain RAG 챗봇 (메모리 버전) 초기화 중...{Style.RESET_ALL}")

        # LLM 초기화
        self.llm = get_llm(model_name="solar-pro", temperature=0.7)

        # 임베딩 초기화
        self.embeddings = get_embeddings(model_name="solar-embedding-1-large")

        # Retriever 초기화
        self.retriever = HybridRetriever(
            vector_db_path="./data/chroma_db",
            sqlite_db_path="./data/langchain.db"
        )

        # 대화 관리자 초기화
        self.conversation_manager = ConversationManager(
            llm=self.llm,
            memory_type="buffer_window",
            window_size=10
        )

        # 대화 히스토리
        self.conversation_history = []

        print(f"{Fore.GREEN}✅ 시스템 초기화 완료!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 연속 질문이 가능합니다. 이전 대화 내용을 참조할 수 있습니다.{Style.RESET_ALL}")

    def format_conversation_context(self, max_turns: int = 5) -> str:
        """대화 컨텍스트 포맷팅"""
        if not self.conversation_history:
            return ""

        # 최근 대화만 사용
        recent = self.conversation_history[-max_turns*2:] if len(self.conversation_history) > max_turns*2 else self.conversation_history

        context = "이전 대화:\n"
        for entry in recent:
            role = "사용자" if entry["role"] == "user" else "어시스턴트"
            content = entry["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            context += f"{role}: {content}\n"

        return context

    def chat(self, query: str) -> str:
        """사용자 질문에 대한 응답 생성"""

        # 문서 검색
        docs = self.retriever.search(query, k=5)

        # 컨텍스트 생성
        context = ""
        sources = []

        if docs:
            context = "\n\n".join([doc.page_content[:500] for doc in docs])
            for doc in docs[:3]:
                title = doc.metadata.get('title', 'Unknown')
                sources.append(title)

        # 대화 히스토리 컨텍스트
        conversation_context = self.format_conversation_context()

        # 프롬프트 구성
        prompt = f"""당신은 LangChain 전문가 AI 어시스턴트입니다.
아래 제공된 컨텍스트와 이전 대화를 참고하여 사용자의 질문에 답변해주세요.

{conversation_context}

현재 참고 문서:
{context}

현재 질문: {query}

지침:
1. 이전 대화 맥락을 고려하여 답변하세요
2. "그것", "이것", "위의" 등의 지시어는 이전 대화 내용을 참조합니다
3. 연속된 질문인 경우 이전 답변을 확장하여 설명하세요
4. 한국어로 친절하게 답변하세요

답변:"""

        # 응답 생성
        response = self.llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)

        # 대화 히스토리에 추가
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})

        # 대화 관리자에도 저장
        self.conversation_manager.add_user_message(query)
        self.conversation_manager.add_assistant_message(answer)

        return answer, sources

    def run_interactive(self):
        """대화형 모드 실행"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💬 대화형 모드 시작 (종료: 'quit', 'exit', 'q'){Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

        session_start = datetime.now()

        while True:
            try:
                # 사용자 입력
                user_input = input(f"{Fore.GREEN}👤 You: {Style.RESET_ALL}")

                # 종료 명령 체크
                if user_input.lower() in ['quit', 'exit', 'q', '종료']:
                    break

                # 대화 초기화 명령
                if user_input.lower() in ['clear', 'reset', '초기화']:
                    self.conversation_history = []
                    self.conversation_manager.clear()
                    print(f"{Fore.YELLOW}🔄 대화가 초기화되었습니다.{Style.RESET_ALL}\n")
                    continue

                # 도움말
                if user_input.lower() in ['help', '도움말', '?']:
                    self.show_help()
                    continue

                # 응답 생성
                print(f"{Fore.YELLOW}🤔 생각 중...{Style.RESET_ALL}")
                answer, sources = self.chat(user_input)

                # 응답 출력
                print(f"\n{Fore.CYAN}🤖 Bot:{Style.RESET_ALL}")
                print(answer)

                # 출처 표시
                if sources:
                    print(f"\n{Fore.BLUE}📚 참고 문서:{Style.RESET_ALL}")
                    for source in sources:
                        print(f"  - {source}")

                print(f"\n{Fore.GRAY}{'-'*60}{Style.RESET_ALL}\n")

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️ 대화 중단됨{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}❌ 오류: {e}{Style.RESET_ALL}\n")

        # 세션 종료
        session_duration = datetime.now() - session_start
        turns = len(self.conversation_history) // 2

        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 세션 통계{Style.RESET_ALL}")
        print(f"  - 대화 턴: {turns}회")
        print(f"  - 소요 시간: {session_duration}")
        print(f"  - 평균 응답 길이: {self.conversation_manager.get_statistics().get('avg_assistant_length', 0):.0f}자")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}👋 대화를 종료합니다. 감사합니다!{Style.RESET_ALL}")

    def show_help(self):
        """도움말 표시"""
        help_text = f"""
{Fore.CYAN}📖 도움말{Style.RESET_ALL}

{Fore.YELLOW}기본 명령:{Style.RESET_ALL}
  • quit, exit, q - 대화 종료
  • clear, reset - 대화 초기화
  • help, ? - 이 도움말 표시

{Fore.YELLOW}연속 질문 예제:{Style.RESET_ALL}
  1. "LangChain이란 무엇인가요?"
  2. "그것의 주요 구성 요소는?"
  3. "더 자세히 설명해주세요"
  4. "예제 코드를 보여주세요"

{Fore.YELLOW}팁:{Style.RESET_ALL}
  • 이전 대화를 참조할 때 "그것", "이것", "위의" 등을 사용하세요
  • "더 자세히", "예를 들어" 등으로 추가 설명을 요청할 수 있습니다
  • 관련된 새 주제로 자연스럽게 전환 가능합니다
"""
        print(help_text)


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="대화 메모리가 있는 LangChain 챗봇")
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="단일 질문 모드"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="컬러 출력 비활성화"
    )

    args = parser.parse_args()

    if args.no_color:
        # 컬러 비활성화
        Fore.CYAN = Fore.GREEN = Fore.YELLOW = Fore.RED = Fore.BLUE = Fore.GRAY = ""
        Style.RESET_ALL = ""

    try:
        chatbot = MemoryChatbot()

        if args.question:
            # 단일 질문 모드
            answer, sources = chatbot.chat(args.question)
            print(f"\n{Fore.CYAN}답변:{Style.RESET_ALL}")
            print(answer)
            if sources:
                print(f"\n{Fore.BLUE}참고 문서:{Style.RESET_ALL}")
                for source in sources:
                    print(f"  - {source}")
        else:
            # 대화형 모드
            chatbot.run_interactive()

    except Exception as e:
        print(f"{Fore.RED}❌ 시스템 오류: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()