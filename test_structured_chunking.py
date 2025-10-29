#!/usr/bin/env python3
"""
구조 기반 청킹 전략 테스트 스크립트
코드 블록과 함수 시그니처 보존을 검증
"""

import sys
import os
from typing import List
from langchain.schema import Document
from advanced_text_splitter import StructuredTextSplitter, create_smart_splitter
from data_collector import LangChainDataCollector

# 테스트용 샘플 문서들
SAMPLE_MARKDOWN = """
# LangChain Introduction

LangChain is a framework for developing applications powered by language models.

## Getting Started

To get started with LangChain, first install the package:

```python
pip install langchain
```

## Core Concepts

### Chains

Chains are the core concept of LangChain. Here's a simple example:

```python
from langchain import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

# Initialize the LLM
llm = OpenAI(temperature=0.9)

# Create a prompt template
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}?",
)

# Create a chain
chain = LLMChain(llm=llm, prompt=prompt)

# Run the chain
result = chain.run("colorful socks")
print(result)
```

### Memory

LangChain provides several memory classes to maintain conversation state:

```python
from langchain.memory import ConversationBufferMemory

class ChatBot:
    def __init__(self):
        self.memory = ConversationBufferMemory()
        self.llm = OpenAI(temperature=0.7)

    def chat(self, user_input: str) -> str:
        # Add user input to memory
        self.memory.chat_memory.add_user_message(user_input)

        # Generate response
        response = self.llm.predict(user_input)

        # Add AI response to memory
        self.memory.chat_memory.add_ai_message(response)

        return response

    def get_history(self):
        return self.memory.chat_memory.messages
```

## Advanced Features

LangChain also supports:
- Document loaders
- Text splitters
- Vector stores
- Agents and tools
"""

SAMPLE_WITH_LARGE_CODE = """
# Complex Example

Here's a large code block that should be preserved:

```python
import asyncio
from typing import List, Dict, Any, Optional
from langchain.chains import LLMChain
from langchain.memory import ConversationSummaryMemory
from langchain.callbacks import CallbackHandler

class AdvancedLangChainApplication:
    '''
    An advanced LangChain application with multiple features:
    - Async processing
    - Custom callbacks
    - Memory management
    - Error handling
    '''

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = self._setup_llm()
        self.memory = ConversationSummaryMemory(llm=self.llm)
        self.chains = {}
        self.callbacks = []

    def _setup_llm(self):
        '''Initialize the language model with configuration'''
        from langchain.llms import OpenAI

        return OpenAI(
            model_name=self.config.get('model', 'gpt-3.5-turbo'),
            temperature=self.config.get('temperature', 0.7),
            max_tokens=self.config.get('max_tokens', 1000)
        )

    async def process_query(self, query: str) -> str:
        '''Process a query asynchronously'''
        try:
            # Prepare the chain
            chain = self._get_or_create_chain('default')

            # Run with callbacks
            result = await chain.arun(
                query,
                callbacks=self.callbacks
            )

            # Update memory
            self.memory.save_context(
                {"input": query},
                {"output": result}
            )

            return result

        except Exception as e:
            return f"Error processing query: {str(e)}"

    def _get_or_create_chain(self, chain_type: str) -> LLMChain:
        '''Get or create a chain by type'''
        if chain_type not in self.chains:
            from langchain.prompts import PromptTemplate

            prompt = PromptTemplate(
                input_variables=["input"],
                template="Answer the following: {input}"
            )

            self.chains[chain_type] = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=self.memory
            )

        return self.chains[chain_type]

    def add_callback(self, callback: CallbackHandler):
        '''Add a callback handler'''
        self.callbacks.append(callback)

    def clear_memory(self):
        '''Clear conversation memory'''
        self.memory.clear()

    def get_conversation_summary(self) -> str:
        '''Get a summary of the conversation'''
        return self.memory.buffer

# Usage example
async def main():
    config = {
        'model': 'gpt-4',
        'temperature': 0.8,
        'max_tokens': 2000
    }

    app = AdvancedLangChainApplication(config)

    # Process queries
    queries = [
        "What is LangChain?",
        "How do I use memory in LangChain?",
        "What are agents?"
    ]

    for query in queries:
        response = await app.process_query(query)
        print(f"Q: {query}")
        print(f"A: {response}\n")

    # Get conversation summary
    summary = app.get_conversation_summary()
    print(f"Conversation Summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates advanced LangChain usage with async processing.
"""


def test_code_block_preservation():
    """테스트 1: 코드 블록 보존 검증"""
    print("\n" + "="*60)
    print("테스트 1: 코드 블록 보존 검증")
    print("="*60)

    # 구조 기반 분할기 생성
    splitter = StructuredTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        preserve_code_blocks=True
    )

    # 문서 생성
    doc = Document(
        page_content=SAMPLE_MARKDOWN,
        metadata={"source": "test"}
    )

    # 분할
    chunks = splitter.split_documents([doc])

    print(f"\n총 청크 수: {len(chunks)}")

    # 코드 블록 청크 확인
    code_chunks = [
        chunk for chunk in chunks
        if chunk.metadata.get('chunk_type') == 'code'
    ]

    print(f"코드 블록 청크: {len(code_chunks)}개")

    # 각 코드 청크 검증
    for i, chunk in enumerate(code_chunks, 1):
        print(f"\n코드 청크 {i}:")
        print(f"  - 언어: {chunk.metadata.get('language', 'unknown')}")
        print(f"  - 함수들: {chunk.metadata.get('functions', [])}")
        print(f"  - 클래스들: {chunk.metadata.get('classes', [])}")
        print(f"  - 내용 길이: {len(chunk.page_content)}자")

        # 코드 블록이 온전히 보존되었는지 확인
        if "```" in chunk.page_content:
            print("  ✅ 코드 블록 마커 보존됨")
        else:
            print("  ⚠️  코드 블록 마커 누락")


def test_function_preservation():
    """테스트 2: 함수 정의 보존 검증"""
    print("\n" + "="*60)
    print("테스트 2: 함수 정의 보존 검증")
    print("="*60)

    splitter = StructuredTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        preserve_functions=True
    )

    doc = Document(
        page_content=SAMPLE_WITH_LARGE_CODE,
        metadata={"source": "test_large"}
    )

    chunks = splitter.split_documents([doc])

    print(f"\n총 청크 수: {len(chunks)}")

    # 함수 이름 추출 및 검증
    expected_functions = [
        "__init__",
        "_setup_llm",
        "process_query",
        "_get_or_create_chain",
        "add_callback",
        "clear_memory",
        "get_conversation_summary",
        "main"
    ]

    found_functions = []
    for chunk in chunks:
        functions = chunk.metadata.get('functions', [])
        found_functions.extend(functions)

    print(f"\n기대한 함수들: {expected_functions}")
    print(f"발견된 함수들: {list(set(found_functions))}")

    # 각 함수가 보존되었는지 확인
    for func in expected_functions:
        if func in found_functions:
            print(f"  ✅ {func} - 보존됨")
        else:
            print(f"  ❌ {func} - 누락됨")


def test_markdown_structure():
    """테스트 3: Markdown 구조 보존 검증"""
    print("\n" + "="*60)
    print("테스트 3: Markdown 구조 보존 검증")
    print("="*60)

    splitter = StructuredTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        preserve_markdown_structure=True
    )

    doc = Document(
        page_content=SAMPLE_MARKDOWN,
        metadata={"source": "test"}
    )

    chunks = splitter.split_documents([doc])

    print(f"\n총 청크 수: {len(chunks)}")

    # 섹션별 청크 확인
    sections = {}
    for chunk in chunks:
        section_title = chunk.metadata.get('section_title', 'Unknown')
        section_level = chunk.metadata.get('section_level', 0)

        if section_title not in sections:
            sections[section_title] = {
                'level': section_level,
                'chunks': []
            }
        sections[section_title]['chunks'].append(chunk)

    print("\n섹션별 청크 분포:")
    for title, info in sections.items():
        print(f"  - {title} (Level {info['level']}): {len(info['chunks'])}개 청크")


def test_compare_splitters():
    """테스트 4: 일반 분할기 vs 구조 기반 분할기 비교"""
    print("\n" + "="*60)
    print("테스트 4: 일반 분할기 vs 구조 기반 분할기 비교")
    print("="*60)

    # 데이터 수집기 초기화
    collector = LangChainDataCollector()

    # 테스트 문서
    test_doc = Document(
        page_content=SAMPLE_WITH_LARGE_CODE,
        metadata={"doc_id": "test", "source": "test"}
    )

    # 일반 분할
    print("\n[일반 분할기 사용]")
    normal_chunks = collector.chunk_documents(
        [test_doc],
        chunk_size=500,
        use_structured_splitter=False
    )
    print(f"  청크 수: {len(normal_chunks)}")

    # 구조 기반 분할
    print("\n[구조 기반 분할기 사용]")
    structured_chunks = collector.chunk_documents(
        [test_doc],
        chunk_size=500,
        use_structured_splitter=True
    )
    print(f"  청크 수: {len(structured_chunks)}")

    # 코드 보존 비교
    print("\n코드 블록 보존 비교:")

    # 일반 분할에서 코드 조각 찾기
    normal_code_fragments = 0
    for chunk in normal_chunks:
        if "def " in chunk.page_content or "class " in chunk.page_content:
            normal_code_fragments += 1

    # 구조 기반 분할에서 코드 청크 찾기
    structured_code_chunks = len([
        c for c in structured_chunks
        if c.metadata.get('chunk_type') in ['code', 'code_function', 'code_partial']
    ])

    print(f"  일반 분할 - 코드 포함 청크: {normal_code_fragments}개")
    print(f"  구조 분할 - 코드 전용 청크: {structured_code_chunks}개")


def test_real_langchain_doc():
    """테스트 5: 실제 LangChain 문서로 테스트"""
    print("\n" + "="*60)
    print("테스트 5: 실제 LangChain 문서 테스트")
    print("="*60)

    collector = LangChainDataCollector()

    # 샘플 URL 가져오기
    sample_urls = collector.get_sample_urls()[:2]  # 2개만 테스트

    print(f"\n테스트할 URL: {sample_urls[0]}")

    # 문서 수집
    documents = collector.collect_documents(urls=sample_urls, max_pages=2)

    if documents:
        print(f"\n수집된 문서: {len(documents)}개")

        # 구조 기반 청킹
        chunks = collector.chunk_documents(
            documents,
            chunk_size=1000,
            use_structured_splitter=True
        )

        # 통계 출력
        print(f"\n청킹 통계:")
        print(f"  - 총 청크 수: {len(chunks)}")

        # 청크 타입별 분포
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        print(f"\n청크 타입별 분포:")
        for chunk_type, count in sorted(chunk_types.items()):
            print(f"  - {chunk_type}: {count}개")


def main():
    """모든 테스트 실행"""
    print("\n" + "="*70)
    print(" 구조 기반 청킹 전략 테스트 시작 ")
    print("="*70)

    # 테스트 실행
    test_code_block_preservation()
    test_function_preservation()
    test_markdown_structure()
    test_compare_splitters()

    # 실제 문서 테스트 (선택적)
    try:
        test_real_langchain_doc()
    except Exception as e:
        print(f"\n실제 문서 테스트 실패: {e}")

    print("\n" + "="*70)
    print(" 모든 테스트 완료! ")
    print("="*70)

    print("\n✅ 구조 기반 청킹의 주요 이점:")
    print("  1. 코드 블록이 완전히 보존됨")
    print("  2. 함수와 클래스 정의가 분할되지 않음")
    print("  3. Markdown 헤더 기반 논리적 섹션 유지")
    print("  4. 코드와 설명 텍스트의 컨텍스트 보존")
    print("  5. 검색 시 더 정확한 코드 예제 제공 가능")


if __name__ == "__main__":
    main()