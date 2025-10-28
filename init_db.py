#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
SQLite 데이터베이스와 테이블을 생성합니다.
"""

import os
import sqlite3
from pathlib import Path

def init_database():
    """SQLite 데이터베이스 초기화"""

    # 데이터 디렉토리 생성
    db_dir = Path("./data")
    db_dir.mkdir(parents=True, exist_ok=True)

    # 데이터베이스 경로
    db_path = db_dir / "langchain.db"

    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # documents 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id VARCHAR(255) UNIQUE NOT NULL,
            title VARCHAR(500),
            url TEXT,
            category VARCHAR(100),
            module_name VARCHAR(200),
            content TEXT NOT NULL,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # code_examples 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS code_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id VARCHAR(255),
            language VARCHAR(50),
            code TEXT NOT NULL,
            description TEXT,
            imports TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
    """)

    # api_references 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name VARCHAR(200),
            method_name VARCHAR(200),
            parameters TEXT,
            return_type VARCHAR(100),
            description TEXT,
            doc_id VARCHAR(255),
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
    """)

    # conversations 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # messages 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # evaluations 테이블 생성
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

    # 인덱스 생성
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")

    conn.commit()
    conn.close()

    print(f"✅ 데이터베이스 초기화 완료: {db_path}")
    print("✅ 생성된 테이블:")
    print("  - documents")
    print("  - code_examples")
    print("  - api_references")
    print("  - conversations")
    print("  - messages")
    print("  - evaluations")

if __name__ == "__main__":
    init_database()
    print("\n🎉 데이터베이스 초기화가 성공적으로 완료되었습니다!")