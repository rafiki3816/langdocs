"""
Text-to-SQL RAG 모듈
자연어를 SQL로 변환하고 데이터베이스 쿼리 수행
"""

import sqlite3
import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

from langchain.prompts import PromptTemplate
from langchain.schema import Document

from llm import get_llm, get_sql_llm
from prompts import get_sql_generation_template


@dataclass
class SQLResult:
    """SQL 쿼리 결과를 저장하는 데이터 클래스"""
    query: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time: Optional[float] = None


class TextToSQLRAG:
    """Text-to-SQL RAG 시스템"""

    def __init__(
        self,
        db_path: str = "./data/langchain.db",
        llm=None
    ):
        """
        TextToSQLRAG 초기화

        Args:
            db_path: SQLite 데이터베이스 경로
            llm: 사용할 LLM 모델 (없으면 기본 모델 사용)
        """
        self.db_path = db_path
        self.llm = llm or get_sql_llm()
        self.schema = self._extract_database_schema()

    def _extract_database_schema(self) -> str:
        """데이터베이스 스키마 추출"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 모든 테이블 목록 가져오기
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = cursor.fetchall()

            schema_info = []
            for (table_name,) in tables:
                # 테이블 스키마 가져오기
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                table_schema = f"\n테이블: {table_name}\n"
                table_schema += "컬럼:\n"

                for col in columns:
                    col_id, col_name, col_type, not_null, default, is_pk = col
                    table_schema += f"  - {col_name} ({col_type})"
                    if is_pk:
                        table_schema += " [PRIMARY KEY]"
                    if not_null:
                        table_schema += " [NOT NULL]"
                    table_schema += "\n"

                # 샘플 데이터 가져오기 (참고용)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_rows = cursor.fetchall()
                if sample_rows:
                    table_schema += f"샘플 데이터 ({len(sample_rows)}행):\n"
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    col_names = [col[1] for col in cursor.fetchall()]
                    for row in sample_rows[:2]:  # 최대 2행만 표시
                        row_str = ", ".join([f"{col_names[i]}={row[i]}"
                                           for i in range(len(row))])
                        table_schema += f"  {row_str}\n"

                schema_info.append(table_schema)

            conn.close()
            return "\n".join(schema_info)

        except Exception as e:
            print(f"스키마 추출 실패: {e}")
            return ""

    def generate_sql(self, question: str) -> str:
        """
        자연어 질문을 SQL 쿼리로 변환

        Args:
            question: 자연어 질문

        Returns:
            생성된 SQL 쿼리
        """
        # SQL 생성 프롬프트 가져오기
        prompt_template = get_sql_generation_template()

        # 프롬프트 템플릿이 문자열인지 PromptTemplate 객체인지 확인
        if isinstance(prompt_template, PromptTemplate):
            formatted_prompt = prompt_template.format(
                schema=self.schema,
                question=question
            )
        else:
            # 문자열인 경우 직접 포맷팅
            formatted_prompt = prompt_template.format(
                schema=self.schema,
                question=question
            )

        # LLM으로 SQL 생성
        response = self.llm.invoke(formatted_prompt)

        # response가 문자열인지 객체인지 확인
        if hasattr(response, 'content'):
            sql_query = self._extract_sql_from_response(response.content)
        else:
            sql_query = self._extract_sql_from_response(str(response))

        return sql_query

    def _extract_sql_from_response(self, response: str) -> str:
        """LLM 응답에서 SQL 쿼리 추출"""
        # SQL 코드 블록 찾기
        sql_pattern = r'```sql\s*(.*?)\s*```'
        matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        # 코드 블록이 없으면 SELECT로 시작하는 부분 찾기
        select_pattern = r'(SELECT\s+.*?(?:;|$))'
        matches = re.findall(select_pattern, response, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        # 전체 응답 반환 (최후의 수단)
        return response.strip()

    def execute_sql(self, sql_query: str) -> Union[pd.DataFrame, None]:
        """
        SQL 쿼리 실행

        Args:
            sql_query: 실행할 SQL 쿼리

        Returns:
            pandas DataFrame 또는 None (오류 발생 시)
        """
        try:
            # pandas의 read_sql_query를 사용하여 직접 DataFrame으로 변환
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            return df

        except Exception as e:
            print(f"SQL 실행 오류: {e}")
            return None

    def execute_sql_raw(self, sql_query: str) -> SQLResult:
        """
        SQL 쿼리 실행 (원본 SQLResult 반환)

        Args:
            sql_query: 실행할 SQL 쿼리

        Returns:
            쿼리 실행 결과 (SQLResult 객체)
        """
        import time

        start_time = time.time()
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 반환
            cursor = conn.cursor()

            # 쿼리 실행
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            # 결과를 딕셔너리 리스트로 변환
            results = []
            for row in rows:
                results.append(dict(row))

            conn.close()

            execution_time = time.time() - start_time

            return SQLResult(
                query=sql_query,
                results=results,
                execution_time=execution_time
            )

        except Exception as e:
            return SQLResult(
                query=sql_query,
                results=[],
                error=str(e),
                execution_time=time.time() - start_time
            )

    def format_results(self, sql_result: SQLResult, max_rows: int = 10) -> str:
        """
        SQL 결과를 읽기 쉬운 형식으로 포맷

        Args:
            sql_result: SQL 실행 결과
            max_rows: 표시할 최대 행 수

        Returns:
            포맷된 결과 문자열
        """
        if sql_result.error:
            return f"❌ 오류 발생: {sql_result.error}"

        if not sql_result.results:
            return "결과가 없습니다."

        # 결과 포맷팅
        output = []
        output.append(f"✅ {len(sql_result.results)}개 결과 찾음")
        output.append(f"⏱️ 실행 시간: {sql_result.execution_time:.3f}초\n")

        # 테이블 형식으로 출력
        if sql_result.results:
            # 컬럼명 추출
            columns = list(sql_result.results[0].keys())

            # 컬럼 너비 계산
            col_widths = {}
            for col in columns:
                max_width = len(str(col))
                for row in sql_result.results[:max_rows]:
                    max_width = max(max_width, len(str(row.get(col, ''))))
                col_widths[col] = min(max_width, 50)  # 최대 50자

            # 헤더 출력
            header = " | ".join([str(col).ljust(col_widths[col]) for col in columns])
            output.append(header)
            output.append("-" * len(header))

            # 데이터 출력
            for i, row in enumerate(sql_result.results[:max_rows]):
                row_str = " | ".join([
                    str(row.get(col, ''))[:col_widths[col]].ljust(col_widths[col])
                    for col in columns
                ])
                output.append(row_str)

            if len(sql_result.results) > max_rows:
                output.append(f"\n... {len(sql_result.results) - max_rows}개 행 더 있음")

        return "\n".join(output)

    def convert_to_documents(self, sql_result: SQLResult) -> List[Document]:
        """
        SQL 결과를 LangChain Document 객체로 변환

        Args:
            sql_result: SQL 실행 결과

        Returns:
            Document 객체 리스트
        """
        documents = []

        for row in sql_result.results:
            # content 필드가 있으면 사용, 없으면 전체 행을 문자열로
            if 'content' in row:
                page_content = row['content']
            else:
                page_content = ", ".join([f"{k}={v}" for k, v in row.items()])

            # 메타데이터 생성
            metadata = dict(row)
            metadata['source'] = 'sql_query'
            metadata['query'] = sql_result.query

            documents.append(Document(
                page_content=page_content,
                metadata=metadata
            ))

        return documents

    def text_to_sql_rag(
        self,
        question: str,
        execute: bool = True,
        format_output: bool = True,
        return_documents: bool = False
    ) -> Dict[str, Any]:
        """
        Text-to-SQL RAG 파이프라인 실행

        Args:
            question: 자연어 질문
            execute: SQL 실행 여부
            format_output: 결과 포맷팅 여부
            return_documents: Document 객체 반환 여부

        Returns:
            실행 결과 딕셔너리
        """
        result = {
            'question': question,
            'sql_query': None,
            'raw_results': None,
            'formatted_results': None,
            'documents': None,
            'error': None
        }

        try:
            # 1. SQL 생성
            sql_query = self.generate_sql(question)
            result['sql_query'] = sql_query
            print(f"생성된 SQL:\n{sql_query}\n")

            if execute:
                # 2. SQL 실행
                sql_result = self.execute_sql(sql_query)
                result['raw_results'] = sql_result

                if sql_result.error:
                    result['error'] = sql_result.error
                else:
                    # 3. 결과 포맷팅
                    if format_output:
                        formatted = self.format_results(sql_result)
                        result['formatted_results'] = formatted

                    # 4. Document 변환
                    if return_documents:
                        documents = self.convert_to_documents(sql_result)
                        result['documents'] = documents

        except Exception as e:
            result['error'] = str(e)

        return result

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블의 상세 정보 반환"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))

            if not cursor.fetchone():
                return {'error': f"테이블 '{table_name}'이 존재하지 않습니다."}

            # 컬럼 정보
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # 인덱스 정보
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()

            # 행 개수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            conn.close()

            return {
                'table_name': table_name,
                'columns': columns,
                'indexes': indexes,
                'row_count': row_count
            }

        except Exception as e:
            return {'error': str(e)}


# 사용 예제
if __name__ == "__main__":
    print("🔍 Text-to-SQL RAG 테스트\n")

    # Text-to-SQL 시스템 초기화
    text_to_sql = TextToSQLRAG()

    # 테스트 질문들
    test_questions = [
        "documents 테이블에 몇 개의 문서가 있나요?",
        "가장 최근에 생성된 문서 5개를 보여주세요",
        "카테고리별 문서 개수를 알려주세요",
        "제목에 'LangChain'이 포함된 문서를 찾아주세요"
    ]

    for question in test_questions:
        print(f"\n📝 질문: {question}")
        print("-" * 50)

        # Text-to-SQL 실행
        result = text_to_sql.text_to_sql_rag(
            question=question,
            execute=True,
            format_output=True,
            return_documents=True
        )

        # 결과 출력
        if result['error']:
            print(f"❌ 오류: {result['error']}")
        else:
            print(f"SQL: {result['sql_query']}")
            print(f"\n결과:\n{result['formatted_results']}")

            if result['documents']:
                print(f"\n📄 {len(result['documents'])}개 문서 생성됨")

    # 테이블 정보 확인
    print("\n\n📊 테이블 정보")
    print("-" * 50)
    table_info = text_to_sql.get_table_info("documents")
    if 'error' not in table_info:
        print(f"테이블: {table_info['table_name']}")
        print(f"행 개수: {table_info['row_count']}")
        print(f"컬럼 개수: {len(table_info['columns'])}")
    else:
        print(f"오류: {table_info['error']}")

    print("\n✅ Text-to-SQL RAG 테스트 완료!")