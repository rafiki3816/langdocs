#!/usr/bin/env python3
"""
환경변수 및 API 키 테스트 스크립트
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style

# colorama 초기화 (Windows 지원)
init()

# 프로젝트 루트 경로 설정
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# .env 파일 로드
env_path = ROOT_DIR / '.env'
load_dotenv(env_path)

def print_status(name: str, value: str, is_set: bool = True):
    """상태를 색상과 함께 출력"""
    if is_set and value and value != "your-actual-api-key-here":
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}"
        value_display = f"{value[:10]}..." if len(value) > 10 else value
    else:
        status = f"{Fore.RED}✗{Style.RESET_ALL}"
        value_display = "Not set" if not value else "Default value"

    print(f"{status} {name}: {value_display}")

def test_environment_variables():
    """환경변수 설정 확인"""
    print(f"\n{Fore.CYAN}=== 환경변수 설정 확인 ==={Style.RESET_ALL}\n")

    required_vars = {
        "UPSTAGE_API_KEY": "Upstage API Key",
        "DATABASE_URL": "Database URL",
        "CHROMA_PERSIST_DIRECTORY": "ChromaDB Directory",
        "APP_ENV": "Application Environment",
        "LLM_MODEL": "LLM Model",
        "EMBEDDING_MODEL": "Embedding Model"
    }

    all_set = True

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        is_valid = bool(value) and not value.startswith("your-")
        print_status(description, value or "", is_valid)

        if not is_valid:
            all_set = False

    return all_set

def test_upstage_connection():
    """Upstage API 연결 테스트"""
    print(f"\n{Fore.CYAN}=== Upstage API 연결 테스트 ==={Style.RESET_ALL}\n")

    api_key = os.getenv("UPSTAGE_API_KEY")

    if not api_key or api_key == "your-actual-api-key-here":
        print(f"{Fore.YELLOW}⚠ Upstage API 키가 설정되지 않았습니다.{Style.RESET_ALL}")
        print(f"  1. https://console.upstage.ai 에서 API 키를 발급받으세요.")
        print(f"  2. .env 파일의 UPSTAGE_API_KEY를 업데이트하세요.")
        return False

    try:
        from langchain_upstage import ChatUpstage

        # 간단한 연결 테스트
        llm = ChatUpstage(
            api_key=api_key,
            model=os.getenv("LLM_MODEL", "solar-1-mini-chat")
        )

        # 최소한의 테스트 호출
        response = llm.invoke("Hi")

        print(f"{Fore.GREEN}✓ Upstage API 연결 성공!{Style.RESET_ALL}")
        print(f"  - 모델: {os.getenv('LLM_MODEL')}")
        print(f"  - 응답 길이: {len(response.content)} characters")
        return True

    except ImportError:
        print(f"{Fore.RED}✗ langchain-upstage 패키지가 설치되지 않았습니다.{Style.RESET_ALL}")
        print(f"  실행: pip install langchain-upstage")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ API 연결 실패: {str(e)}{Style.RESET_ALL}")
        return False

def test_database_config():
    """데이터베이스 설정 확인"""
    print(f"\n{Fore.CYAN}=== 데이터베이스 설정 확인 ==={Style.RESET_ALL}\n")

    db_url = os.getenv("DATABASE_URL")

    if not db_url or "your-" in db_url or "password" in db_url:
        print(f"{Fore.YELLOW}⚠ 데이터베이스 URL이 기본값입니다.{Style.RESET_ALL}")
        print(f"  실제 데이터베이스 정보로 업데이트가 필요합니다.")
        return False

    try:
        from sqlalchemy import create_engine

        # 연결 테스트 (실제 연결은 하지 않음)
        engine = create_engine(db_url, connect_args={"connect_timeout": 5})

        print(f"{Fore.GREEN}✓ 데이터베이스 URL 형식이 올바릅니다.{Style.RESET_ALL}")

        # DB 타입 확인
        if "mysql" in db_url:
            print(f"  - 타입: MySQL")
        elif "postgresql" in db_url:
            print(f"  - 타입: PostgreSQL")
        else:
            print(f"  - 타입: {db_url.split(':')[0]}")

        return True

    except ImportError:
        print(f"{Fore.YELLOW}⚠ SQLAlchemy가 설치되지 않았습니다.{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}✗ 데이터베이스 설정 오류: {str(e)}{Style.RESET_ALL}")
        return False

def test_project_structure():
    """프로젝트 구조 확인"""
    print(f"\n{Fore.CYAN}=== 프로젝트 구조 확인 ==={Style.RESET_ALL}\n")

    required_dirs = [
        "src",
        "data",
        "scripts",
        "tests",
        "config",
        "docs",
        "data/raw",
        "data/processed",
        "data/embeddings",
        "venv"
    ]

    all_exists = True

    for dir_name in required_dirs:
        dir_path = ROOT_DIR / dir_name
        exists = dir_path.exists()

        if exists:
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} {dir_name}/")
        else:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {dir_name}/ (missing)")
            all_exists = False

    return all_exists

def check_dependencies():
    """필수 패키지 설치 확인"""
    print(f"\n{Fore.CYAN}=== 필수 패키지 확인 ==={Style.RESET_ALL}\n")

    packages = {
        "langchain": "LangChain",
        "langchain_community": "LangChain Community",
        "langchain_upstage": "LangChain Upstage",
        "chromadb": "ChromaDB",
        "sqlalchemy": "SQLAlchemy",
        "dotenv": "python-dotenv",
        "bs4": "BeautifulSoup4",
        "streamlit": "Streamlit",
        "fastapi": "FastAPI"
    }

    all_installed = True

    for package, name in packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} {name}")
        except ImportError:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {name} (not installed)")
            all_installed = False

    return all_installed

def main():
    """메인 테스트 실행"""
    print(f"\n{Fore.BLUE}{'='*50}")
    print(f"   LangChain Chatbot 환경 설정 테스트")
    print(f"{'='*50}{Style.RESET_ALL}")

    results = {
        "프로젝트 구조": test_project_structure(),
        "환경변수": test_environment_variables(),
        "필수 패키지": check_dependencies(),
        "데이터베이스": test_database_config(),
        "Upstage API": test_upstage_connection()
    }

    # 결과 요약
    print(f"\n{Fore.CYAN}=== 테스트 결과 요약 ==={Style.RESET_ALL}\n")

    all_passed = True
    for test_name, result in results.items():
        if result:
            print(f"{Fore.GREEN}✓{Style.RESET_ALL} {test_name}: PASS")
        else:
            print(f"{Fore.RED}✗{Style.RESET_ALL} {test_name}: FAIL")
            all_passed = False

    # 최종 메시지
    print(f"\n{Fore.BLUE}{'='*50}{Style.RESET_ALL}")

    if all_passed:
        print(f"{Fore.GREEN}🎉 모든 테스트 통과! 개발을 시작할 준비가 완료되었습니다.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ 일부 설정이 필요합니다. 위의 메시지를 확인하세요.{Style.RESET_ALL}")
        print(f"\n다음 단계:")
        print(f"1. Upstage API 키 발급: https://console.upstage.ai")
        print(f"2. .env 파일 업데이트")
        print(f"3. 누락된 패키지 설치: pip install -r requirements.txt")

    print(f"{Fore.BLUE}{'='*50}{Style.RESET_ALL}\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())