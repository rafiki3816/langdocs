"""프롬프트 템플릿 모듈
시스템 프롬프트 및 컨텍스트 포맷팅"""

from langchain.prompts import ChatPromptTemplate, PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from typing import Dict, List, Any


#==========SystemPrompts==========

LANGCHAIN_EXPERT_PROMPT="""당신은 LangChain 전문가 문서 AI 어시스턴트입니다.
LangChain 문서에서 정확하고 유용한 정보를 제공하는 것이 당신의 역할입니다.

다음 지침을 따르세요:
1. 제공된 컨텍스트를 기반으로 정확하게 답변하세요.
2. 코드나 API 사용법을 설명할 때는 예시를 포함하세요.
3. 답변은 간결하면서도 충분히 상세하게 작성하세요.
4. 확실하지 않은 정보는 추측하지 말고 모른다고 말하세요.
5. 컨텍스트에 답이 없으면 문서를 더 찾아보라고 제안하세요.
6. LangChain 컴포넌트 간의 관계와 사용 방법을 명확히 설명하세요.
7. 질문에 대한 답변이 문서에 없다면 일반적인 프로그래밍 지식으로 도움을 주되 출처를 명시하세요."""

SQL_GENERATION_PROMPT="""당신은 SQL 쿼리 생성 전문가입니다.
자연어 질문을 받아 적절한 SQL 쿼리를 생성하는 것이 당신의 역할입니다.

데이터베이스 스키마:
{schema}

다음 규칙을 따르세요:
1. 표준 SQL 문법을 사용하세요.
2. 테이블과 컬럼 이름은 스키마에 정의된 것만 사용하세요.
3. 필요한 경우 JOIN을 사용하여 여러 테이블을 연결하세요.
4. WHERE 절을 사용하여 적절한 필터링을 수행하세요.
5. 결과 수를 제한해야 하는 경우 LIMIT를 사용하세요.
6. 가능한 한 효율적인 쿼리를 생성하세요.
7. 주석을 포함하여 쿼리의 목적을 설명하세요."""

EVALUATION_PROMPT="""당신은 RAG 시스템 평가 전문가입니다.
생성된 답변의 품질을 평가하고 개선점을 제시하는 것이 당신의 역할입니다.

평가 기준:
1. 정확성: 제공된 컨텍스트와 일치하는가?
2. 관련성: 질문에 직접적으로 답변하는가?
3. 완성도: 충분히 상세하고 이해하기 쉬운가?
4. 정확성: 사실적으로 정확한가?
5. 유용성: 실제로 도움이 되는 정보인가?

각 기준에 대해 1-5점 척도로 평가하고, 총점과 개선 제안을 제공하세요."""


#==========PromptTemplates==========

def get_rag_prompt_template() -> ChatPromptTemplate:
    """
    RAG 시스템용 프롬프트 템플릿을 반환합니다.

    Returns:
        ChatPromptTemplate: RAG 프롬프트 템플릿
    """
    template = ChatPromptTemplate.from_messages([
        ("system", LANGCHAIN_EXPERT_PROMPT),
        ("human", """다음 컨텍스트 정보를 참고하여 질문에 답변해주세요.

컨텍스트:
{context}

질문: {question}

답변:""")
    ])
    return template


def get_sql_generation_template() -> PromptTemplate:
    """
    SQL 생성용 프롬프트 템플릿을 반환합니다.

    Returns:
        PromptTemplate: SQL 생성 프롬프트 템플릿
    """
    template = PromptTemplate(
        input_variables=["schema", "question"],
        template=SQL_GENERATION_PROMPT + "\n\n질문: {question}\n\nSQL:"
    )
    return template


def get_conversation_prompt_template() -> ChatPromptTemplate:
    """
    대화형 RAG 시스템용 프롬프트 템플릿을 반환합니다.

    Returns:
        ChatPromptTemplate: 대화형 프롬프트 템플릿
    """
    template = ChatPromptTemplate.from_messages([
        ("system", LANGCHAIN_EXPERT_PROMPT),
        ("human", """이전 대화 내용:
{chat_history}

관련 컨텍스트:
{context}

질문: {question}

이전 대화와 컨텍스트를 고려하여 답변해주세요.""")
    ])
    return template


def get_evaluation_template() -> PromptTemplate:
    """
    답변 평가용 프롬프트 템플릿을 반환합니다.

    Returns:
        PromptTemplate: 평가 프롬프트 템플릿
    """
    template = PromptTemplate(
        input_variables=["question", "answer", "context"],
        template=EVALUATION_PROMPT + """

질문: {question}

제공된 컨텍스트:
{context}

생성된 답변:
{answer}

평가:"""
    )
    return template


#==========Few-shotExamples==========

def get_langchain_examples() -> List[Dict[str, str]]:
    """
    LangChain 관련 Few-shot 예시를 반환합니다.

    Returns:
        예시 리스트
    """
    examples = [
        {
            "question": "LangChain이란 무엇인가?",
            "answer": "LangChain은 대규모 언어 모델(LLM)을 사용하는 애플리케이션을 개발하기 위한 프레임워크입니다. "
                     "체인(Chains), 에이전트(Agents), 도구(Tools) 등의 컴포넌트를 제공하여 "
                     "복잡한 LLM 기반 애플리케이션을 쉽게 구축할 수 있도록 돕습니다."
        },
        {
            "question": "LCEL이란 무엇인가?",
            "answer": "LCEL(LangChain Expression Language)은 LangChain에서 제공하는 선언적 언어입니다. "
                     "파이프(|) 연산자를 사용하여 여러 컴포넌트를 쉽게 연결할 수 있으며, "
                     "복잡한 체인을 간결하고 읽기 쉬운 코드로 표현할 수 있습니다."
        },
        {
            "question": "벡터 스토어는 어떻게 사용하나?",
            "answer": "벡터 스토어는 문서를 임베딩으로 변환하여 저장하고 검색하는 시스템입니다. "
                     "문서를 작은 청크로 나누고, Chroma나 FAISS 같은 벡터 데이터베이스에 저장합니다. "
                     "검색 시에는 쿼리를 임베딩으로 변환한 후 유사한 문서를 찾아 반환합니다."
        }
    ]
    return examples


def get_few_shot_prompt_template() -> FewShotPromptTemplate:
    """
    Few-shot 학습용 프롬프트 템플릿을 반환합니다.

    Returns:
        FewShotPromptTemplate: Few-shot 프롬프트 템플릿
    """
    examples = get_langchain_examples()

    example_prompt = PromptTemplate(
        input_variables=["question", "answer"],
        template="질문: {question}\n답변: {answer}"
    )

    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix=LANGCHAIN_EXPERT_PROMPT + "\n\n다음은 좋은 답변의 예시입니다:",
        suffix="\n\n컨텍스트:\n{context}\n\n질문: {question}\n답변:",
        input_variables=["context", "question"]
    )

    return few_shot_prompt


#==========CustomPromptFunctions==========

def format_context(documents: List[Any], max_length: int = 3000) -> str:
    """
    검색된 문서들을 컨텍스트 문자열로 포맷팅합니다.

    Args:
        documents: 문서 리스트
        max_length: 최대 컨텍스트 길이

    Returns:
        포맷팅된 컨텍스트 문자열
    """
    context_parts = []
    current_length = 0

    for i, doc in enumerate(documents, 1):
        # Document 객체에서 내용 추출
        if hasattr(doc, 'page_content'):
            content = doc.page_content
        else:
            content = str(doc)

        # 메타데이터에서 출처 정보 추출
        if hasattr(doc, 'metadata'):
            source = doc.metadata.get('source', 'unknown')
            header = f"[문서 {i} 출처: {source}]"
        else:
            header = f"[문서 {i}]"

        part = f"{header}\n{content}\n"

        # 길이 제한 체크
        if current_length + len(part) > max_length:
            if current_length == 0:  # 첫 문서도 너무 길면
                context_parts.append(part[:max_length])
            break

        context_parts.append(part)
        current_length += len(part)

    return "\n".join(context_parts)


def format_chat_history(messages: List[Dict[str, str]], max_turns: int = 5) -> str:
    """
    채팅 기록을 포맷팅합니다.

    Args:
        messages: 메시지 딕셔너리 리스트
        max_turns: 포함할 최대 대화 턴 수

    Returns:
        포맷팅된 채팅 기록
    """
    if not messages:
        return "없음"

    # 최근 대화만 선택
    recent_messages = messages[-max_turns*2:] if len(messages) > max_turns*2 else messages

    formatted = []
    for msg in recent_messages:
        role = "사용자" if msg.get("role") == "user" else "어시스턴트"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


def get_system_prompt() -> str:
    """
    시스템 프롬프트 반환

    Returns:
        시스템 프롬프트 문자열
    """
    return LANGCHAIN_EXPERT_PROMPT


def get_prompt_by_type(prompt_type: str) -> Any:
    """
    프롬프트 타입에 따라 적절한 템플릿을 반환합니다.

    Args:
        prompt_type: 프롬프트 타입 ("rag", "sql", "conversation", "evaluation", "few_shot")

    Returns:
        해당하는 프롬프트 템플릿

    Raises:
        ValueError: 지원하지 않는 프롬프트 타입
    """
    prompt_map = {
        "rag": get_rag_prompt_template,
        "sql": get_sql_generation_template,
        "conversation": get_conversation_prompt_template,
        "evaluation": get_evaluation_template,
        "few_shot": get_few_shot_prompt_template
    }

    if prompt_type not in prompt_map:
        raise ValueError(f"지원하지 않는 프롬프트 타입: {prompt_type}")

    return prompt_map[prompt_type]()


if __name__ == "__main__":
    # 모듈 테스트
    print("===== Prompts 모듈 테스트 =====\n")

    # 1. RAG 프롬프트 테스트
    print("1. RAG 프롬프트 템플릿")
    rag_prompt = get_rag_prompt_template()
    print(f"입력 변수: {rag_prompt.input_variables}")

    # 2. SQL 프롬프트 테스트
    print("\n2. SQL 생성 프롬프트")
    sql_prompt = get_sql_generation_template()
    test_sql = sql_prompt.format(
        schema="CREATE TABLE documents (id INT, title VARCHAR(255), content TEXT)",
        question="가장 최근 문서 5개를 가져오는 쿼리"
    )
    print(f"생성된 프롬프트 예시: {test_sql[:200]}...")

    # 3. Few-shot 예시 테스트
    print("\n3. Few-shot 예시")
    examples = get_langchain_examples()
    print(f"예시 개수: {len(examples)}")
    print(f"첫 번째 질문: {examples[0]['question']}")

    # 4. 컨텍스트 포맷팅 테스트
    print("\n4. 컨텍스트 포맷팅")
    from langchain.schema import Document
    test_docs = [
        Document(page_content="테스트 문서 1", metadata={"source": "test1.md"}),
        Document(page_content="테스트 문서 2", metadata={"source": "test2.md"})
    ]
    formatted = format_context(test_docs)
    print(f"포맷팅된 컨텍스트:\n{formatted}")

    print("\n모든 테스트 완료!")
