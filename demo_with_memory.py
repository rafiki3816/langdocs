#!/usr/bin/env python3
"""
Streamlit 기반 LangChain RAG 챗봇 데모 (대화 메모리 기능 포함)
연속 질문을 처리할 수 있는 향상된 버전
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import get_llm, get_embeddings
from vector_database import VectorDatabase
from retriever import HybridRetriever
from conversation import ConversationManager
from text_to_sql import TextToSQLRAG
import sqlite3
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="LangChain RAG 챗봇 (메모리 버전)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
    <style>
    .stChat {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    .source-card {
        background-color: #e8eaf6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #3f51b5;
    }
    .context-info {
        background-color: #fff3e0;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'conversation_manager' not in st.session_state:
    st.session_state.conversation_manager = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = []
if 'text_to_sql' not in st.session_state:
    st.session_state.text_to_sql = None

def initialize_system():
    """시스템 초기화"""
    with st.spinner("🔄 시스템을 초기화하는 중..."):
        try:
            # LLM 초기화
            st.session_state.llm = get_llm(
                model_name="solar-pro",
                temperature=0.7
            )

            # 임베딩 초기화
            st.session_state.embeddings = get_embeddings(
                model_name="solar-embedding-1-large"
            )

            # Retriever 초기화
            st.session_state.retriever = HybridRetriever(
                vector_db_path="./data/chroma_db",
                sqlite_db_path="./data/langchain.db"
            )

            # 대화 관리자 초기화
            st.session_state.conversation_manager = ConversationManager(
                llm=st.session_state.llm,
                memory_type="buffer_window",
                window_size=10  # 최근 10개 대화만 기억
            )

            # Text-to-SQL 초기화
            st.session_state.text_to_sql = TextToSQLRAG(
                llm=st.session_state.llm,
                db_path="./data/langchain.db"
            )

            st.success("✅ 시스템이 성공적으로 초기화되었습니다!")
            return True
        except Exception as e:
            st.error(f"❌ 초기화 실패: {str(e)}")
            return False

def format_conversation_context(messages: List[Dict], max_turns: int = 5) -> str:
    """대화 컨텍스트를 포맷팅"""
    if not messages:
        return ""

    # 최근 max_turns 개의 대화만 사용
    recent_messages = messages[-max_turns*2:] if len(messages) > max_turns*2 else messages

    context = "이전 대화 내용:\n"
    for msg in recent_messages:
        role = "사용자" if msg["role"] == "user" else "어시스턴트"
        # 긴 메시지는 축약
        content = msg["content"]
        if len(content) > 200:
            content = content[:200] + "..."
        context += f"{role}: {content}\n"

    return context

def generate_response_with_memory(query: str, context: str, conversation_history: str) -> str:
    """대화 메모리를 포함한 응답 생성"""

    # 프롬프트 구성
    prompt = f"""당신은 LangChain 전문가 AI 어시스턴트입니다.
아래 제공된 컨텍스트와 이전 대화 내용을 참고하여 사용자의 질문에 답변해주세요.

{conversation_history}

현재 컨텍스트:
{context}

현재 질문: {query}

지침:
1. 이전 대화 맥락을 고려하여 답변하세요
2. 사용자가 "그것", "이것", "위의" 등 지시대명사를 사용하면 이전 대화에서 언급된 내용을 참고하세요
3. 연속된 질문인 경우 이전 답변을 바탕으로 더 자세히 설명하세요
4. 컨텍스트에 없는 내용은 추론하지 말고 모른다고 답하세요

답변:"""

    response = st.session_state.llm.invoke(prompt)

    # 대화 관리자가 있으면 대화 기록 저장
    if st.session_state.conversation_manager:
        st.session_state.conversation_manager.add_user_message(query)
        st.session_state.conversation_manager.add_assistant_message(response.content if hasattr(response, 'content') else str(response))

    return response.content if hasattr(response, 'content') else str(response)

def clear_conversation():
    """대화 초기화"""
    st.session_state.messages = []
    st.session_state.conversation_context = []
    if st.session_state.conversation_manager:
        st.session_state.conversation_manager.clear()
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")

    # 시스템 초기화
    if st.button("🚀 시스템 초기화", type="primary"):
        initialize_system()

    # 대화 초기화
    if st.button("🗑️ 대화 초기화"):
        clear_conversation()
        st.rerun()

    st.divider()

    # 검색 설정
    st.subheader("🔍 검색 설정")
    search_k = st.slider("검색 문서 수", min_value=1, max_value=10, value=5)
    show_sources = st.checkbox("출처 표시", value=True)
    show_context = st.checkbox("컨텍스트 표시", value=False)

    st.divider()

    # 메모리 설정
    st.subheader("🧠 메모리 설정")
    use_memory = st.checkbox("대화 메모리 사용", value=True)
    memory_window = st.slider("메모리 윈도우 크기", min_value=2, max_value=20, value=10)

    st.divider()

    # 통계
    st.subheader("📊 통계")

    # 문서 수 확인
    try:
        conn = sqlite3.connect('./data/langchain.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        conn.close()
        st.metric("총 문서 수", f"{doc_count}개")
    except:
        st.metric("총 문서 수", "N/A")

    st.metric("대화 턴 수", len(st.session_state.messages) // 2)

    if st.session_state.conversation_manager:
        stats = st.session_state.conversation_manager.get_statistics()
        if stats:
            st.metric("평균 응답 길이", f"{stats.get('avg_assistant_length', 0):.0f}자")

# 메인 화면
st.title("🤖 LangChain RAG 챗봇 (메모리 강화 버전)")
st.markdown("### 💡 연속 질문이 가능한 지능형 대화 시스템")

# 대화 메모리 상태 표시
if use_memory and st.session_state.conversation_manager:
    with st.expander("🧠 대화 메모리 상태", expanded=False):
        memory_info = st.session_state.conversation_manager.get_memory_string()
        if memory_info:
            st.text(memory_info)
        else:
            st.info("아직 대화 기록이 없습니다")

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["💬 채팅", "📚 예제 질문", "❓ 사용법", "🔍 SQL 쿼리"])

with tab1:
    # 시스템 체크
    if not st.session_state.llm:
        st.warning("⚠️ 시스템이 초기화되지 않았습니다. 사이드바에서 '시스템 초기화' 버튼을 클릭하세요.")

    # 대화 기록 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 소스 표시 (어시스턴트 메시지만)
                if message["role"] == "assistant" and "sources" in message and show_sources:
                    with st.expander("📚 참고 문서", expanded=False):
                        for source in message.get("sources", []):
                            st.markdown(f"- {source}")

    # 입력 창
    if prompt := st.chat_input("질문을 입력하세요... (연속 질문 가능)"):
        if not st.session_state.llm:
            st.error("❌ 먼저 시스템을 초기화해주세요!")
        else:
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(prompt)

            # 어시스턴트 응답 생성
            with st.chat_message("assistant"):
                with st.spinner("생각 중..."):
                    try:
                        # 문서 검색
                        docs = []
                        if st.session_state.retriever:
                            docs = st.session_state.retriever.search(prompt, k=search_k)

                        # 컨텍스트 생성
                        context = ""
                        sources = []

                        if docs:
                            context = "\n\n".join([doc.page_content[:500] for doc in docs])

                            # 소스 정보 수집
                            for doc in docs[:3]:
                                title = doc.metadata.get('title', 'Unknown')
                                url = doc.metadata.get('url', '#')
                                sources.append(f"[{title}]({url})")

                        # 대화 히스토리 준비
                        conversation_history = ""
                        if use_memory:
                            conversation_history = format_conversation_context(
                                st.session_state.messages[:-1],  # 현재 메시지 제외
                                max_turns=memory_window
                            )

                        # 응답 생성
                        if context or conversation_history:
                            response = generate_response_with_memory(
                                prompt,
                                context,
                                conversation_history
                            )
                        else:
                            # 컨텍스트가 없으면 일반 응답
                            response = st.session_state.llm.invoke(
                                f"LangChain 전문가로서 답변해주세요: {prompt}"
                            )
                            response = response.content if hasattr(response, 'content') else str(response)

                        # 응답 표시
                        st.markdown(response)

                        # 컨텍스트 정보 표시
                        if show_context and context:
                            st.markdown(
                                f'<div class="context-info">📄 {len(docs)}개 문서 참조</div>',
                                unsafe_allow_html=True
                            )

                        # 어시스턴트 메시지 저장
                        message_data = {"role": "assistant", "content": response}
                        if sources:
                            message_data["sources"] = sources
                        st.session_state.messages.append(message_data)

                    except Exception as e:
                        error_msg = f"❌ 오류 발생: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

with tab2:
    st.header("📚 연속 질문 예제")

    st.markdown("""
    ### 기본 질문 후 연속 질문 예제:

    **첫 번째 질문:**
    - "LangChain이란 무엇인가요?"

    **연속 질문들:**
    - "그것의 주요 구성 요소는 무엇인가요?"
    - "더 자세히 설명해주세요"
    - "예제 코드를 보여주세요"
    - "Agent에 대해서도 설명해주세요"
    - "방금 설명한 Agent와 Tool의 차이는?"

    ### RAG 관련 연속 질문:

    **첫 번째 질문:**
    - "RAG 시스템의 작동 원리를 설명해주세요"

    **연속 질문들:**
    - "그렇다면 벡터 검색은 어떻게 작동하나요?"
    - "임베딩은 어떻게 생성되나요?"
    - "ChromaDB는 뭔가요?"
    - "다른 벡터 DB도 사용할 수 있나요?"

    ### Memory 관련 연속 질문:

    **첫 번째 질문:**
    - "LangChain의 메모리 종류를 설명해주세요"

    **연속 질문들:**
    - "ConversationBufferMemory는 뭔가요?"
    - "그것과 ConversationSummaryMemory의 차이는?"
    - "언제 어떤 것을 사용해야 하나요?"
    - "코드 예제를 보여주세요"
    """)

    if st.button("🔄 예제 질문으로 시작하기"):
        st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": "LangChain이란 무엇인가요?"})
        st.rerun()

with tab3:
    st.header("❓ 사용법")

    st.markdown("""
    ### 🚀 시작하기

    1. **시스템 초기화**: 사이드바에서 '시스템 초기화' 버튼 클릭
    2. **질문하기**: 채팅 입력창에 질문 입력
    3. **연속 질문**: 이전 대화를 참조하여 추가 질문 가능

    ### 💡 연속 질문 팁

    - **지시대명사 사용**: "그것", "이것", "위의" 등을 사용하여 이전 내용 참조
    - **추가 설명 요청**: "더 자세히", "예제 포함해서" 등으로 확장된 답변 요청
    - **관련 주제 전환**: 이전 답변과 관련된 새로운 주제로 자연스럽게 전환

    ### ⚙️ 설정 옵션

    - **대화 메모리 사용**: 이전 대화 컨텍스트를 기억
    - **메모리 윈도우**: 기억할 대화 턴 수 설정
    - **검색 문서 수**: 각 질문에 대해 검색할 문서 개수
    - **출처 표시**: 답변의 근거가 된 문서 표시

    ### 📊 현재 상태

    - 총 문서: 63개 (LangChain 공식 문서)
    - 카테고리: 12개 주제
    - 메모리 타입: ConversationBufferWindowMemory
    """)

with tab4:
    st.header("🔍 SQL 쿼리 실행")

    st.markdown("""
    ### 데이터베이스 쿼리 기능
    자연어로 질문하거나 직접 SQL을 입력하여 데이터베이스를 조회할 수 있습니다.
    """)

    # SQL 모드 선택
    sql_mode = st.radio(
        "쿼리 모드 선택",
        ["자연어 → SQL", "직접 SQL 입력"],
        horizontal=True
    )

    if sql_mode == "자연어 → SQL":
        st.markdown("#### 자연어로 데이터베이스 질문하기")

        # 예제 질문들
        example_questions = [
            "모든 문서의 제목을 보여주세요",
            "API Reference 카테고리의 문서는 몇 개인가요?",
            "가장 최근에 추가된 문서 5개를 보여주세요",
            "코드 예제가 있는 문서들을 보여주세요",
            "대화 기록을 최신 순으로 10개 보여주세요",
            "평가 점수가 가장 높은 결과를 보여주세요"
        ]

        selected_example = st.selectbox("예제 질문 선택", ["직접 입력"] + example_questions)

        if selected_example != "직접 입력":
            nl_query = selected_example
        else:
            nl_query = st.text_area("자연어 질문 입력", height=100)

        if st.button("🔄 SQL로 변환 및 실행", key="nl_to_sql"):
            if not st.session_state.text_to_sql:
                st.error("❌ 먼저 시스템을 초기화해주세요!")
            elif nl_query:
                try:
                    with st.spinner("SQL 쿼리 생성 중..."):
                        # SQL 생성
                        generated_sql = st.session_state.text_to_sql.generate_sql(nl_query)

                        # 생성된 SQL 표시
                        st.code(generated_sql, language="sql")

                        # SQL 실행
                        with st.spinner("쿼리 실행 중..."):
                            result_df = st.session_state.text_to_sql.execute_sql(generated_sql)

                            if result_df is not None and not result_df.empty:
                                st.success(f"✅ {len(result_df)}개의 결과를 찾았습니다.")

                                # 결과 표시
                                st.dataframe(result_df, use_container_width=True)

                                # 결과 다운로드 옵션
                                csv = result_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 CSV 다운로드",
                                    data=csv,
                                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.info("결과가 없습니다.")

                except Exception as e:
                    st.error(f"❌ 오류 발생: {str(e)}")
            else:
                st.warning("⚠️ 질문을 입력해주세요.")

    else:  # 직접 SQL 입력
        st.markdown("#### SQL 쿼리 직접 입력")

        # 테이블 정보 표시
        with st.expander("📊 테이블 스키마 보기", expanded=False):
            st.markdown("""
            **주요 테이블:**
            - `documents`: 문서 정보 (id, title, url, content, category, created_at)
            - `conversations`: 대화 세션 (id, session_id, created_at, updated_at)
            - `messages`: 대화 메시지 (id, conversation_id, role, content, timestamp)
            - `code_examples`: 코드 예제 (id, doc_id, language, code, description)
            - `api_references`: API 참조 (id, doc_id, api_name, parameters, returns)
            - `conversation_history`: 대화 기록 (id, session_id, user_message, assistant_message)
            - `evaluations`: 평가 결과 (id, question, answer, score, feedback, timestamp)
            """)

        # SQL 입력
        sql_query = st.text_area(
            "SQL 쿼리 입력",
            height=150,
            placeholder="SELECT * FROM documents LIMIT 10;"
        )

        if st.button("▶️ SQL 실행", key="execute_sql"):
            if not st.session_state.text_to_sql:
                st.error("❌ 먼저 시스템을 초기화해주세요!")
            elif sql_query:
                try:
                    with st.spinner("쿼리 실행 중..."):
                        # SQL 실행
                        result_df = st.session_state.text_to_sql.execute_sql(sql_query)

                        if result_df is not None and not result_df.empty:
                            st.success(f"✅ {len(result_df)}개의 결과를 찾았습니다.")

                            # 결과 표시
                            st.dataframe(result_df, use_container_width=True)

                            # 결과 다운로드 옵션
                            csv = result_df.to_csv(index=False)
                            st.download_button(
                                label="📥 CSV 다운로드",
                                data=csv,
                                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("결과가 없습니다.")

                except Exception as e:
                    st.error(f"❌ 오류 발생: {str(e)}")
            else:
                st.warning("⚠️ SQL 쿼리를 입력해주세요.")

    # 쿼리 히스토리 (선택사항)
    st.divider()
    st.markdown("### 📜 최근 쿼리 예제")

    example_queries = {
        "문서 통계": "SELECT category, COUNT(*) as count FROM documents GROUP BY category ORDER BY count DESC",
        "최신 문서": "SELECT title, category, created_at FROM documents ORDER BY created_at DESC LIMIT 5",
        "코드 예제 수": "SELECT d.title, COUNT(ce.id) as code_count FROM documents d LEFT JOIN code_examples ce ON d.id = ce.doc_id GROUP BY d.id, d.title ORDER BY code_count DESC",
        "대화 통계": "SELECT DATE(timestamp) as date, COUNT(*) as message_count FROM messages GROUP BY DATE(timestamp) ORDER BY date DESC LIMIT 7"
    }

    for name, query in example_queries.items():
        with st.expander(f"📝 {name}"):
            st.code(query, language="sql")
            if st.button(f"실행", key=f"run_{name}"):
                try:
                    result_df = st.session_state.text_to_sql.execute_sql(query)
                    if result_df is not None and not result_df.empty:
                        st.dataframe(result_df, use_container_width=True)
                    else:
                        st.info("결과가 없습니다.")
                except Exception as e:
                    st.error(f"오류: {str(e)}")

# 푸터
st.divider()
st.markdown(
    f"🤖 LangChain RAG 챗봇 v2.0 | 세션 ID: {st.session_state.session_id} | "
    f"대화 메모리: {'활성' if use_memory else '비활성'}"
)