import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationMemory:
    """대화 메모리를 SQLite로 관리하는 경량 헬퍼.

    - 사용자별 별도 DB 파일에 메시지를 저장합니다.
    - 파일 컨텍스트(업로드 파일 정보)도 함께 저장해 맥락 유지에 사용합니다.
    - 최근 N개 조회, 전체 조회, 삭제 등의 기본 기능을 제공합니다.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.db_path = Path(f"data/conversations_{user_id}.db")
        self.init_db()

    def init_db(self):
        """DB 파일 및 테이블이 없으면 생성합니다."""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        logging.debug("conversations table ensured at %s", self.db_path)

    def add_message(self, role: str, content: str, file_context: Optional[Dict[str, Any]] = None):
        """메시지를 DB에 저장합니다.

        Args:
            role: 'user' | 'assistant' | 'system'
            content: 메시지 본문
            file_context: 파일 관련 보조 정보(선택)
        """
        file_context_json = json.dumps(file_context, ensure_ascii=False) if file_context else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO conversations (user_id, role, content, file_context)
                VALUES (?, ?, ?, ?)
                """,
                (self.user_id, role, content, file_context_json),
            )
            conn.commit()

    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최신 메시지부터 limit개를 가져와 시간순으로 반환합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT role, content, file_context, timestamp
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (self.user_id, limit),
            )
            messages: List[Dict[str, Any]] = []
            for row in reversed(cursor.fetchall()):
                file_context = json.loads(row["file_context"]) if row["file_context"] else None
                messages.append(
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "file_context": file_context,
                        "timestamp": row["timestamp"],
                    }
                )
            return messages

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """전체 대화 기록을 오래된 순으로 반환합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT role, content, file_context, timestamp
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp ASC
                """,
                (self.user_id,),
            )
            messages: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                file_context = json.loads(row["file_context"]) if row["file_context"] else None
                messages.append(
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "file_context": file_context,
                        "timestamp": row["timestamp"],
                    }
                )
            return messages

    def enhance_message_with_file_context(self, message: str, current_file_info: Optional[Dict[str, Any]]) -> str:
        """사용자 표현(예: "내가 올린 파일")을 실제 파일명으로 치환합니다."""
        if not current_file_info:
            return message
        file_references = [
            "내가 올린 파일",
            "업로드한 파일",
            "올린 파일",
            "이 파일",
            "현재 파일",
            "업로드된 파일",
        ]
        enhanced_message = message
        filename = current_file_info.get("filename", "unknown")
        for ref in file_references:
            if ref in message:
                enhanced_message = enhanced_message.replace(ref, f"{filename} 파일")
        return enhanced_message

    def get_file_aware_context(self, current_file_info: Optional[Dict[str, Any]]) -> str:
        """현재 파일 정보를 요약 텍스트로 구성해 제공합니다."""
        if not current_file_info:
            return "현재 업로드된 파일이 없습니다."
        parts = [f"현재 분석 중인 파일: {current_file_info.get('filename', '알 수 없음')}"]
        if "columns" in current_file_info:
            parts.append(f"컬럼: {', '.join(current_file_info['columns'][:5])}...")
        if "shape_total" in current_file_info:
            shape = current_file_info["shape_total"]
            if shape:
                parts.append(f"크기: {shape[0]}행 x {shape[1]}열")
        return " | ".join(parts)

    def clear_conversation(self):
        """현재 사용자 대화 기록을 모두 삭제합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations WHERE user_id = ?", (self.user_id,))
            conn.commit()


def get_memory(user_id: str = "default") -> ConversationMemory:
    """팩토리 함수: 사용자별 메모리 인스턴스를 반환합니다."""
    return ConversationMemory(user_id)
