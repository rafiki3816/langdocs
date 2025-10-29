#!/usr/bin/env python3
"""
SQL 쿼리 탭 기능 테스트
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import get_llm
from text_to_sql import TextToSQLRAG

def test_sql_query_functionality():
    """SQL 쿼리 기능 테스트"""
    print("=" * 60)
    print("🔍 SQL 쿼리 기능 테스트")
    print("=" * 60)

    # LLM 초기화
    print("\n1. LLM 초기화...")
    llm = get_llm(model="solar-pro", temperature=0.3)
    print("✅ LLM 초기화 완료")

    # Text-to-SQL 초기화
    print("\n2. Text-to-SQL 시스템 초기화...")
    text_to_sql = TextToSQLRAG(llm=llm, db_path="./data/langchain.db")
    print("✅ Text-to-SQL 초기화 완료")

    # 테스트 1: 자연어 → SQL 변환
    print("\n3. 자연어 → SQL 변환 테스트")
    test_questions = [
        "모든 문서의 제목을 보여주세요",
        "API Reference 카테고리의 문서는 몇 개인가요?",
        "가장 최근에 추가된 문서 5개를 보여주세요"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n  [{i}] 질문: {question}")
        try:
            # SQL 생성
            sql = text_to_sql.generate_sql(question)
            print(f"  생성된 SQL: {sql}")

            # SQL 실행
            result = text_to_sql.execute_sql(sql)
            if result is not None and not result.empty:
                print(f"  결과: {len(result)}개 행 반환")
                print(f"  샘플 데이터:\n{result.head(3)}")
            else:
                print("  결과: 데이터 없음")

        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")

    # 테스트 2: 직접 SQL 실행
    print("\n4. 직접 SQL 실행 테스트")
    test_queries = [
        "SELECT COUNT(*) as total FROM documents",
        "SELECT category, COUNT(*) as count FROM documents GROUP BY category ORDER BY count DESC LIMIT 5",
        "SELECT title, created_at FROM documents ORDER BY created_at DESC LIMIT 3"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n  [{i}] SQL: {query}")
        try:
            result = text_to_sql.execute_sql(query)
            if result is not None and not result.empty:
                print(f"  결과:\n{result}")
            else:
                print("  결과: 데이터 없음")
        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")

    # 테스트 3: 테이블 정보 확인
    print("\n5. 데이터베이스 테이블 정보 확인")
    table_info_query = """
    SELECT name FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """

    try:
        result = text_to_sql.execute_sql(table_info_query)
        if result is not None and not result.empty:
            print(f"  테이블 목록:")
            for table_name in result['name'].values:
                print(f"    - {table_name}")

                # 각 테이블의 행 수 확인
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_result = text_to_sql.execute_sql(count_query)
                if count_result is not None and not count_result.empty:
                    print(f"      (행 수: {count_result['count'].iloc[0]})")
        else:
            print("  테이블 정보를 찾을 수 없습니다.")
    except Exception as e:
        print(f"  ❌ 오류: {str(e)}")

    print("\n" + "=" * 60)
    print("✅ SQL 쿼리 기능 테스트 완료!")
    print("=" * 60)
    print("\n💡 Streamlit UI에서 SQL 쿼리 탭을 확인하세요:")
    print("   http://localhost:8503")
    print("\n📝 SQL 쿼리 탭 기능:")
    print("   - 자연어 → SQL 변환 모드")
    print("   - 직접 SQL 입력 모드")
    print("   - 쿼리 결과 CSV 다운로드")
    print("   - 예제 쿼리 실행")

if __name__ == "__main__":
    test_sql_query_functionality()