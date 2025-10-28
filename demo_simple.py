"""
Streamlit 데모 애플리케이션 - 간단한 버전
LangChain RAG 챗봇의 웹 인터페이스
"""

import streamlit as st
import os
from datetime import datetime
import time

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="LangChain RAG 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 추가
st.markdown("""
<style>
    .stChat {
        padding: 20px;
    }
    .user-message {
        background-color: #E8F4FD;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .assistant-message {
        background-color: #F0F0F0;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = None

# 사이드바 설정
with st.sidebar:
    st.title("⚙️ 설정")

    # 시스템 상태
    st.markdown("### 📊 시스템 상태")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 시스템 초기화"):
            with st.spinner("초기화 중..."):
                try:
                    from llm import get_llm
                    from vector_database import VectorDatabase
                    from retriever import HybridRetriever

                    # LLM 초기화
                    st.session_state.llm = get_llm()

                    # 벡터 DB 초기화
                    st.session_state.vector_db = VectorDatabase()
                    st.session_state.vector_db.init_vectorstore()

                    # Retriever 초기화
                    st.session_state.retriever = HybridRetriever(st.session_state.vector_db)

                    st.success("✅ 시스템 초기화 완료!")
                except Exception as e:
                    st.error(f"❌ 초기화 실패: {str(e)}")

    with col2:
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.session_state.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.success("✅ 대화 초기화 완료!")

    # 시스템 정보
    st.markdown("---")
    st.markdown("### 📈 시스템 정보")

    if st.session_state.llm:
        st.success("✅ LLM 연결됨")
    else:
        st.warning("⚠️ LLM 미연결")

    if st.session_state.vector_db:
        st.success("✅ 벡터 DB 연결됨")
    else:
        st.warning("⚠️ 벡터 DB 미연결")

    if st.session_state.retriever:
        st.success("✅ 검색 시스템 준비됨")
    else:
        st.warning("⚠️ 검색 시스템 미준비")

    # 검색 설정
    st.markdown("---")
    st.markdown("### 🔍 검색 설정")

    search_k = st.slider(
        "검색할 문서 수",
        min_value=1,
        max_value=10,
        value=3,
        help="더 많은 문서를 검색하면 정확도가 높아지지만 속도가 느려집니다."
    )

    temperature = st.slider(
        "창의성 (Temperature)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="0에 가까울수록 일관성 있고, 1에 가까울수록 창의적입니다."
    )

    # 대화 통계
    st.markdown("---")
    st.markdown("### 📊 대화 통계")
    st.info(f"대화 ID: {st.session_state.conversation_id[:20]}...")
    st.info(f"메시지 수: {len(st.session_state.messages)}")

    # 정보
    st.markdown("---")
    st.markdown("### ℹ️ 정보")
    st.markdown("""
    **LangChain RAG 챗봇 v1.0**

    - 🤖 LLM: Upstage Solar
    - 💾 Vector DB: ChromaDB
    - 📚 문서: LangChain Docs

    [GitHub](https://github.com) | [문서](https://docs.example.com)
    """)

# 메인 화면
st.title("🤖 LangChain RAG 챗봇")
st.markdown("LangChain 문서 기반 지능형 Q&A 시스템")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["💬 채팅", "📚 문서 관리", "📈 통계"])

with tab1:
    # 채팅 인터페이스

    # 시스템 체크
    if not st.session_state.llm:
        st.warning("⚠️ 시스템이 초기화되지 않았습니다. 사이드바에서 '시스템 초기화' 버튼을 클릭하세요.")

    # 대화 기록 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 입력 창
    if prompt := st.chat_input("질문을 입력하세요..."):
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
                        if st.session_state.retriever:
                            docs = st.session_state.retriever.search(prompt, k=search_k)

                            if docs:
                                # 컨텍스트 생성
                                context = "\n\n".join([doc.page_content[:500] for doc in docs])

                                # 소스 정보
                                sources = []
                                for doc in docs[:3]:
                                    title = doc.metadata.get('title', 'Unknown')
                                    category = doc.metadata.get('category', 'Unknown')
                                    sources.append(f"- {title} [{category}]")

                                # 프롬프트 생성
                                full_prompt = f"""다음 컨텍스트를 바탕으로 질문에 한국어로 답변해주세요.

컨텍스트:
{context}

질문: {prompt}

답변:"""

                                # LLM 호출
                                response = st.session_state.llm.invoke(full_prompt)
                                answer = response.content if hasattr(response, 'content') else str(response)

                                # 답변 표시
                                st.markdown(answer)

                                # 소스 정보 표시
                                if sources:
                                    with st.expander("📚 참조 문서"):
                                        st.markdown("\n".join(sources))
                            else:
                                answer = "관련 문서를 찾을 수 없습니다. 다른 질문을 해주세요."
                                st.markdown(answer)
                        else:
                            # 검색 시스템 없이 LLM만 사용
                            response = st.session_state.llm.invoke(prompt)
                            answer = response.content if hasattr(response, 'content') else str(response)
                            st.markdown(answer)
                            st.info("💡 검색 시스템이 초기화되지 않아 일반 응답을 제공합니다.")

                        # 응답 저장
                        st.session_state.messages.append({"role": "assistant", "content": answer})

                    except Exception as e:
                        error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

with tab2:
    st.header("📚 문서 관리")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 문서 수집")

        urls_input = st.text_area(
            "수집할 URL (한 줄에 하나씩)",
            value="https://python.langchain.com/docs/introduction\nhttps://python.langchain.com/docs/concepts",
            height=100
        )

        if st.button("🔄 문서 수집 시작"):
            if urls_input:
                urls = [url.strip() for url in urls_input.split('\n') if url.strip()]

                with st.spinner(f"{len(urls)}개 문서 수집 중..."):
                    try:
                        from data_collector import LangChainDataCollector

                        collector = LangChainDataCollector()
                        documents = collector.collect_documents(urls=urls, max_pages=len(urls))

                        if documents:
                            # 청크 분할
                            chunked_docs = collector.chunk_documents(documents)

                            # 벡터 DB에 저장
                            if st.session_state.vector_db:
                                st.session_state.vector_db.add_documents(chunked_docs)
                                st.success(f"✅ {len(documents)}개 문서, {len(chunked_docs)}개 청크 저장 완료!")
                            else:
                                st.warning("⚠️ 벡터 DB가 초기화되지 않았습니다.")
                        else:
                            st.error("❌ 문서 수집 실패")

                    except Exception as e:
                        st.error(f"❌ 오류: {str(e)}")

    with col2:
        st.subheader("📊 데이터베이스 통계")

        if st.button("📈 통계 조회"):
            try:
                from data_collector import LangChainDataCollector

                collector = LangChainDataCollector()
                stats = collector.get_statistics()

                st.metric("총 문서 수", stats.get('total_documents', 0))

                if stats.get('documents_by_category'):
                    st.markdown("**카테고리별 문서:**")
                    for category, count in stats['documents_by_category'].items():
                        st.info(f"- {category}: {count}개")

                if st.session_state.vector_db:
                    vdb_stats = st.session_state.vector_db.get_statistics()
                    st.metric("벡터 DB 문서 수", vdb_stats.get('document_count', 0))

            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

with tab3:
    st.header("📈 시스템 통계")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 대화 수", len(st.session_state.messages) // 2)
        st.metric("현재 세션 메시지", len(st.session_state.messages))

    with col2:
        st.metric("LLM 상태", "연결됨 ✅" if st.session_state.llm else "미연결 ❌")
        st.metric("Vector DB 상태", "연결됨 ✅" if st.session_state.vector_db else "미연결 ❌")

    with col3:
        st.metric("검색 시스템", "준비됨 ✅" if st.session_state.retriever else "미준비 ❌")
        st.metric("Temperature", temperature)

    # 최근 대화
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("📝 최근 대화")

        for i in range(len(st.session_state.messages)-1, max(-1, len(st.session_state.messages)-6), -1):
            msg = st.session_state.messages[i]
            if msg["role"] == "user":
                st.markdown(f"**👤 사용자:** {msg['content'][:100]}...")
            else:
                st.markdown(f"**🤖 챗봇:** {msg['content'][:100]}...")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    LangChain RAG 챗봇 v1.0 | Powered by Upstage Solar & ChromaDB
    </div>
    """,
    unsafe_allow_html=True
)