"""대화 관리 모듈
대화 기록 저장 및 메모리 관리"""

import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from llm import get_llm
from prompts import format_chat_history


@dataclass
class ConversationTurn:
    """대화 턴 데이터 클래스"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]=None


class ConversationManager:
    """멀티턴 대화를 함수하는 클래스"""

    def __init__(
        self,
        session_id: str=None,
        db_path: str="./data/langchain.db",
        memory_type: str="buffer",
        max_turns: int=10
        ):
        """
        ConversationManager초기화

        Args:
            session_id:세션ID(None이면자동생성)
            db_path:SQLite데이터 베이스경로
            memory_type:메모리변수("buffer","summary","window")
            max_turns:최대 대화 턴 수
        """
        self.session_id=session_id or self._generate_session_id()
        self.db_path=db_path
        self.max_turns=max_turns
        self.conversation_history: List[ConversationTurn]=[]

        #LangChain메모리초기화
        self.memory=self._init_memory(memory_type)

        #DB테이블생성
        self._init_database()

        #기존대화로드(있으면)
        if session_id:
            self._load_conversation()

    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _init_database(self):
        """데이터베이스테이블생성"""
        conn=sqlite3.connect(self.db_path)
        cursor=conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(255),
            role VARCHAR(50),
            content TEXT,
            metadata TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id
        ON conversation_history(session_id)
        """)

        conn.commit()
        conn.close()

    def _init_memory(self, memory_type: str) -> Any:
        """LangChain메모리초기화"""
        llm=get_llm()

        if memory_type=="buffer":
            return ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
        elif memory_type=="window":
            return ConversationBufferWindowMemory(
                return_messages=True,
                memory_key="chat_history",
                k=self.max_turns
            )
        elif memory_type=="summary":
            return ConversationSummaryMemory(
                llm=llm,
                return_messages=True,
                memory_key="chat_history"
            )
        else:
            #기본값: buffer
            return ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )

    def add_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]]=None
    ) -> ConversationTurn:
        """
        대화턴추가

        Args:
            role:역할("user" or "assistant")
            content:메시지 내용
            metadata:추가메타데이터

        Returns:
            ConversationTurn
        """
        turn=ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )

        #메모리에추가
        self.conversation_history.append(turn)

        #LangChain메모리에추가
        if role=="user":
            self.memory.chat_memory.add_user_message(content)
        else:
            self.memory.chat_memory.add_ai_message(content)

        #DB에저장
        self._save_turn_to_db(turn)

        #최대턴수제한
        if len(self.conversation_history) > self.max_turns*2:
            self.conversation_history=self.conversation_history[-(self.max_turns*2):]

        return turn

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]]=None) -> ConversationTurn:
        """사용자메시지추가"""
        return self.add_turn("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]]=None) -> ConversationTurn:
        """어시스턴트메시지추가"""
        return self.add_turn("assistant", content, metadata)

    def _save_turn_to_db(self, turn: ConversationTurn):
        """대화턴을DB에저장"""
        conn=sqlite3.connect(self.db_path)
        cursor=conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO conversation_history
            (session_id, role, content, metadata, timestamp)
            VALUES(?,?,?,?,?)
            """,(
                self.session_id,
                turn.role,
                turn.content,
                json.dumps(turn.metadata) if turn.metadata else None,
                turn.timestamp
            ))
            conn.commit()
        except Exception as e:
            print(f"대화저장실패:{e}")
            conn.rollback()
        finally:
            conn.close()

    def _load_conversation(self):
        """DB에서대화내역로드"""
        conn=sqlite3.connect(self.db_path)
        cursor=conn.cursor()

        try:
            cursor.execute("""
            SELECT role, content, metadata, timestamp
            FROM conversation_history
            WHERE session_id=?
            ORDER BY timestamp
            """,(self.session_id,))

            rows=cursor.fetchall()

            for role, content, metadata_str, timestamp in rows:
                metadata=json.loads(metadata_str) if metadata_str else {}
                turn=ConversationTurn(
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    metadata=metadata
                )
                self.conversation_history.append(turn)

                #LangChain메모리에추가
                if role=="user":
                    self.memory.chat_memory.add_user_message(content)
                else:
                    self.memory.chat_memory.add_ai_message(content)

        except Exception as e:
            print(f"대화로드실패:{e}")
        finally:
            conn.close()

    def get_context(
        self,
        include_system: bool=False,
        max_turns: Optional[int]=None
    ) -> str:
        """
        대화컨텍스트를문자열로반환

        Args:
            include_system:시스템 메시지 포함 여부
            max_turns:포함할최대턴수

        Returns:
            포맷된대화컨텍스트
        """
        if not self.conversation_history:
            return ""

        turns_to_include=max_turns or self.max_turns
        recent_history=self.conversation_history[-(turns_to_include*2):]

        formatted=[]
        for turn in recent_history:
            if not include_system and turn.role=="system":
                continue
            formatted.append(f"{turn.role}:{turn.content}")

        return "\n".join(formatted)

    def get_formatted_history(self) -> str:
        """포맷된대화내역반환"""
        messages=[
            {"role": turn.role,"content": turn.content}
            for turn in self.conversation_history
        ]
        return format_chat_history(messages, max_turns=self.max_turns)

    def get_messages(self) -> List[BaseMessage]:
        """LangChainMessage형식으로반환"""
        messages=[]
        for turn in self.conversation_history:
            if turn.role=="user":
                messages.append(HumanMessage(content=turn.content))
            else:
                messages.append(AIMessage(content=turn.content))
        return messages

    def get_memory_variables(self) -> Dict[str, Any]:
        """메모리변수반환"""
        return self.memory.load_memory_variables({})

    def clear(self):
        """대화내역초기화"""
        self.conversation_history=[]
        self.memory.clear()

    def summarize(self, llm: Optional[BaseChatModel]=None) -> str:
        """
        대화요약생성

        Args:
            llm:사용할LLM(None이면기본LLM사용)

        Returns:
            대화요약
        """
        if not self.conversation_history:
            return "대화내용이없습니다."

        llm=llm or get_llm()

        #대화내용을문자열로변환
        conversation_text=self.get_context()

        #요약프롬프트
        summary_prompt=f"""다음대화내용을요약해주세요:

{conversation_text}

요약:"""

        #LLM을사용해요약생성
        response=llm.invoke(summary_prompt)
        return response.content

    def get_statistics(self) -> Dict[str, Any]:
        """대화통계반환"""
        user_turns=sum(1 for turn in self.conversation_history if turn.role=="user")
        assistant_turns=sum(1 for turn in self.conversation_history if turn.role=="assistant")

        total_user_chars=sum(
            len(turn.content) for turn in self.conversation_history
            if turn.role=="user"
        )
        total_assistant_chars=sum(
            len(turn.content) for turn in self.conversation_history
            if turn.role=="assistant"
        )

        return {
            "session_id": self.session_id,
            "total_turns": len(self.conversation_history),
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "avg_user_length": total_user_chars/user_turns if user_turns > 0 else 0,
            "avg_assistant_length": total_assistant_chars/assistant_turns if assistant_turns > 0 else 0,
            "first_turn": self.conversation_history[0].timestamp if self.conversation_history else None,
            "last_turn": self.conversation_history[-1].timestamp if self.conversation_history else None
        }

    def export_to_json(self, filepath: str):
        """대화내역을JSON파일로내보내기"""
        export_data={
            "session_id": self.session_id,
            "conversation": [asdict(turn) for turn in self.conversation_history],
            "statistics": self.get_statistics()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"대화내보내기완료:{filepath}")


#헬퍼함수들
def create_conversation_manager(
    session_id: Optional[str]=None,
    memory_type: str="buffer"
) -> ConversationManager:
    """
    대화관리자생성

    Args:
        session_id:세션ID
        memory_type:메모리변수

    Returns:
        ConversationManager인스턴스
    """
    return ConversationManager(session_id=session_id, memory_type=memory_type)


def load_conversation(session_id: str) -> ConversationManager:
    """
    기존대화로드

    Args:
        session_id:세션ID

    Returns:
        ConversationManager인스턴스
    """
    return ConversationManager(session_id=session_id)


if __name__=="__main__":
    #모듈테스트
    print("===ConversationManager테스트===\n")

    #1.새대화시작
    print("1.새대화시작")
    conv_manager=create_conversation_manager()
    print(f"세션ID:{conv_manager.session_id}")

    #2.대화턴추가
    print("\n2.대화턴추가")
    conv_manager.add_user_message("LangChain이란무엇인가?")
    conv_manager.add_assistant_message("LangChain은LLM애플리케이션개발을위한프레임워크입니다.")
    conv_manager.add_user_message("메모리기능도있나요?")
    conv_manager.add_assistant_message("네,다양한메모리,컨텍스트관리기능을제공합니다.")

    #3.대화컨텍스트확인
    print("\n3.대화컨텍스트")
    context=conv_manager.get_context()
    print(context)

    #4.포맷된내역
    print("\n4.포맷된내역")
    formatted=conv_manager.get_formatted_history()
    print(formatted)

    #5.통계확인
    print("\n5.대화통계")
    stats=conv_manager.get_statistics()
    for key, value in stats.items():
        print(f"{key}:{value}")

    #6.대화요약(API키필요)
    print("\n6.대화요약")
    try:
        summary=conv_manager.summarize()
        print(f"요약:{summary[:100]}...")
    except Exception as e:
        print(f"요약생성실패(API키없음):{e}")

    #7.JSON으로내보내기
    print("\n7.JSON내보내기")
    export_path=f"./data/conversation_{conv_manager.session_id}.json"
    conv_manager.export_to_json(export_path)

    print("\n테스트완료!")
