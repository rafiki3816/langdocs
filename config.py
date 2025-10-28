"""환경 설정 모듈
프로젝트 전반의 설정값 관리"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import logging

from utils import read_json_file, write_json_file, load_env_file, get_env_variable


# 로깅 설정
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 모델 설정"""
    model_name: str = "solar-1-mini-chat"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30


@dataclass
class EmbeddingConfig:
    """임베딩 모델 설정"""
    model_name: str = "solar-embedding-1-large"
    dimension: int = 4096
    batch_size: int = 100


@dataclass
class VectorDBConfig:
    """벡터 데이터베이스 모델 설정"""
    type: str = "chromadb"
    persist_directory: str = "./data/chroma_db"
    collection_name: str = "langchain_docs"
    distance_metric: str = "cosine"
    index_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SQLDBConfig:
    """SQL 데이터베이스 모델 설정"""
    type: str = "sqlite"
    database_url: str = "sqlite:///./data/langchain.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False


@dataclass
class RetrieverConfig:
    """Retriever 모델 설정"""
    search_mode: str = "hybrid"  # "hybrid", "vector", "sql"
    top_k: int = 5
    score_threshold: float = 0.7
    rerank: bool = True
    rerank_top_k: int = 10


@dataclass
class ConversationConfig:
    """대화 관리 모델 설정"""
    memory_type: str = "buffer_window"  # "buffer", "summary", "buffer_window"
    window_size: int = 10
    max_token_limit: int = 2000
    summary_prompt: Optional[str] = None


@dataclass
class DataCollectorConfig:
    """데이터 수집 모델 설정"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_depth: int = 2
    delay_between_requests: float = 1.0
    user_agent: str = "Mozilla/5.0 (LangChain Documentation Bot)"
    timeout: int = 10


@dataclass
class EvaluatorConfig:
    """평가 모델 설정"""
    evaluation_metrics: List[str] = field(default_factory=lambda: [
        "relevance", "accuracy", "completeness", "retrieval_precision", "retrieval_recall"
    ])
    save_reports: bool = True
    report_directory: str = "./data/evaluation_reports"
    batch_size: int = 10


@dataclass
class StreamlitConfig:
    """Streamlit UI 모델 설정"""
    page_title: str = "LangChain 문서 챗봇"
    page_icon: str = "🤖"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    theme: str = "light"
    show_sources: bool = True
    show_evaluation: bool = False
    enable_sql_mode: bool = True


@dataclass
class LoggingConfig:
    """로깅 모델 설정"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "./logs/app.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class AppConfig:
    """애플리케이션 전체 설정"""
    # API 키
    upstage_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # 모델 설정
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    sql_db: SQLDBConfig = field(default_factory=SQLDBConfig)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    data_collector: DataCollectorConfig = field(default_factory=DataCollectorConfig)
    evaluator: EvaluatorConfig = field(default_factory=EvaluatorConfig)
    streamlit: StreamlitConfig = field(default_factory=StreamlitConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 기타 설정
    debug_mode: bool = False
    data_directory: str = "./data"
    cache_directory: str = "./cache"
    temp_directory: str = "./temp"


class ConfigManager:
    """설정 관리자"""

    def __init__(self, config_path: str = "config.json", env_path: str = ".env"):
        """
        ConfigManager 초기화

        Args:
            config_path: 설정 파일 경로
            env_path: 환경변수 파일 경로
        """
        self.config_path = config_path
        self.env_path = env_path
        self.config = AppConfig()

        # 설정 로드
        self.load_config()

    def load_config(self):
        """설정 로드 (환경변수 -> 설정 파일 -> 기본값 순서)"""
        # 1. 환경변수 파일 로드
        if Path(self.env_path).exists():
            load_env_file(self.env_path)
            logger.info(f"환경변수 파일 로드됨: {self.env_path}")

        # 2. 설정 파일 로드
        if Path(self.config_path).exists():
            config_data = read_json_file(self.config_path)
            self._update_config_from_dict(config_data)
            logger.info(f"설정 파일 로드됨: {self.config_path}")

        # 3. 환경변수에서 API 키 로드 (최우선 순위)
        self._load_api_keys_from_env()

        # 4. 필요한 디렉토리 생성
        self._create_directories()

    def _update_config_from_dict(self, data: Dict[str, Any]):
        """딕셔너리로부터 설정 업데이트"""
        # API 키
        if 'upstage_api_key' in data:
            self.config.upstage_api_key = data['upstage_api_key']
        if 'openai_api_key' in data:
            self.config.openai_api_key = data['openai_api_key']

        # LLM 설정
        if 'llm' in data:
            for key, value in data['llm'].items():
                if hasattr(self.config.llm, key):
                    setattr(self.config.llm, key, value)

        # Embedding 설정
        if 'embedding' in data:
            for key, value in data['embedding'].items():
                if hasattr(self.config.embedding, key):
                    setattr(self.config.embedding, key, value)

        # VectorDB 설정
        if 'vector_db' in data:
            for key, value in data['vector_db'].items():
                if hasattr(self.config.vector_db, key):
                    setattr(self.config.vector_db, key, value)

        # SQL DB 설정
        if 'sql_db' in data:
            for key, value in data['sql_db'].items():
                if hasattr(self.config.sql_db, key):
                    setattr(self.config.sql_db, key, value)

        # Retriever 설정
        if 'retriever' in data:
            for key, value in data['retriever'].items():
                if hasattr(self.config.retriever, key):
                    setattr(self.config.retriever, key, value)

        # Conversation 설정
        if 'conversation' in data:
            for key, value in data['conversation'].items():
                if hasattr(self.config.conversation, key):
                    setattr(self.config.conversation, key, value)

        # Data Collector 설정
        if 'data_collector' in data:
            for key, value in data['data_collector'].items():
                if hasattr(self.config.data_collector, key):
                    setattr(self.config.data_collector, key, value)

        # Evaluator 설정
        if 'evaluator' in data:
            for key, value in data['evaluator'].items():
                if hasattr(self.config.evaluator, key):
                    setattr(self.config.evaluator, key, value)

        # Streamlit 설정
        if 'streamlit' in data:
            for key, value in data['streamlit'].items():
                if hasattr(self.config.streamlit, key):
                    setattr(self.config.streamlit, key, value)

        # Logging 설정
        if 'logging' in data:
            for key, value in data['logging'].items():
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)

        # 기타 설정
        if 'debug_mode' in data:
            self.config.debug_mode = data['debug_mode']
        if 'data_directory' in data:
            self.config.data_directory = data['data_directory']
        if 'cache_directory' in data:
            self.config.cache_directory = data['cache_directory']
        if 'temp_directory' in data:
            self.config.temp_directory = data['temp_directory']

    def _load_api_keys_from_env(self):
        """환경변수에서 API 키 로드"""
        # Upstage API 키
        upstage_key = get_env_variable("UPSTAGE_API_KEY")
        if upstage_key:
            self.config.upstage_api_key = upstage_key
            logger.info("Upstage API 키 로드됨 (환경변수)")

        # OpenAI API 키
        openai_key = get_env_variable("OPENAI_API_KEY")
        if openai_key:
            self.config.openai_api_key = openai_key
            logger.info("OpenAI API 키 로드됨 (환경변수)")

    def _create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            self.config.data_directory,
            self.config.cache_directory,
            self.config.temp_directory,
            self.config.vector_db.persist_directory,
            self.config.evaluator.report_directory,
            Path(self.config.sql_db.database_url.replace("sqlite:///", "")).parent
        ]

        if self.config.logging.file_path:
            directories.append(Path(self.config.logging.file_path).parent)

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

        logger.info("필요한 디렉토리 생성 완료")

    def save_config(self, config_path: Optional[str] = None):
        """설정을 파일로 저장"""
        save_path = config_path or self.config_path

        config_dict = {
            "upstage_api_key": self.config.upstage_api_key,
            "openai_api_key": self.config.openai_api_key,
            "llm": asdict(self.config.llm),
            "embedding": asdict(self.config.embedding),
            "vector_db": asdict(self.config.vector_db),
            "sql_db": asdict(self.config.sql_db),
            "retriever": asdict(self.config.retriever),
            "conversation": asdict(self.config.conversation),
            "data_collector": asdict(self.config.data_collector),
            "evaluator": asdict(self.config.evaluator),
            "streamlit": asdict(self.config.streamlit),
            "logging": asdict(self.config.logging),
            "debug_mode": self.config.debug_mode,
            "data_directory": self.config.data_directory,
            "cache_directory": self.config.cache_directory,
            "temp_directory": self.config.temp_directory
        }

        write_json_file(save_path, config_dict)
        logger.info(f"설정 저장 완료: {save_path}")

    def get_config(self) -> AppConfig:
        """현재 설정 반환"""
        return self.config

    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"설정 업데이트: {key} = {value}")

    def validate_config(self) -> bool:
        """설정 유효성 검사"""
        errors = []

        # API 키 확인
        if not self.config.upstage_api_key:
            errors.append("Upstage API 키가 설정되지 않았습니다.")

        # 디렉토리 존재 확인
        if not Path(self.config.data_directory).exists():
            errors.append(f"데이터 디렉토리가 존재하지 않습니다: {self.config.data_directory}")

        # 데이터베이스 URL 확인
        if not self.config.sql_db.database_url:
            errors.append("데이터베이스 URL이 설정되지 않았습니다.")

        if errors:
            for error in errors:
                logger.error(error)
            return False

        logger.info("설정 유효성 검사 통과")
        return True

    def get_logging_config(self) -> Dict[str, Any]:
        """로깅 설정 딕셔너리 반환"""
        config = {
            'level': getattr(logging, self.config.logging.level),
            'format': self.config.logging.format
        }

        if self.config.logging.file_path:
            config['handlers'] = [
                logging.FileHandler(self.config.logging.file_path),
                logging.StreamHandler()
            ]

        return config

    def reset_to_defaults(self):
        """기본값 설정으로 복원"""
        self.config = AppConfig()
        logger.info("설정이 기본값으로 복원되었습니다.")


# 전역 설정 인스턴스
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """전역 설정 관리자 반환"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """현재 설정 반환"""
    return get_config_manager().get_config()


# 테스트 코드
if __name__ == "__main__":
    print("설정 관리 테스트\n")

    # 설정 관리자 초기화
    config_manager = ConfigManager()

    # 현재 설정 출력
    config = config_manager.get_config()
    print("1단계: 현재 설정")
    print(f"  LLM 모델명: {config.llm.model_name}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Vector DB: {config.vector_db.type}")
    print(f"  검색 모드: {config.retriever.search_mode}")
    print(f"  대화 메모리 타입: {config.conversation.memory_type}")

    # 설정 업데이트
    print("\n2단계: 설정 업데이트")
    config_manager.update_config(debug_mode=True)
    config.llm.temperature = 0.5
    print(f"  Debug 모드: {config.debug_mode}")
    print(f"  새로운 Temperature: {config.llm.temperature}")

    # 설정 저장
    print("\n3단계: 설정 저장")
    test_config_path = "./test_config.json"
    config_manager.save_config(test_config_path)
    print(f"  설정 저장 완료: {test_config_path}")

    # 설정 유효성 검사
    print("\n4단계: 설정 유효성 검사")
    is_valid = config_manager.validate_config()
    print(f"  검증 결과: {'통과' if is_valid else '실패'}")

    # 로깅 설정 확인
    print("\n5단계: 로깅 설정")
    logging_config = config_manager.get_logging_config()
    print(f"  로그 레벨: {config.logging.level}")
    print(f"  로그 포맷: {config.logging.format[:30]}...")

    # 정리
    if Path(test_config_path).exists():
        Path(test_config_path).unlink()
        print(f"\n테스트 파일 제거됨: {test_config_path}")

    print("\n설정 관리 테스트 완료!")
