import logging
import sqlite3
from pathlib import Path


class UserProfile:
    """사용자 프로필(자유 텍스트)을 SQLite로 간단히 저장/조회.

    - '정보' 레코드를 시간순으로 누적 저장합니다.
    - AI 프롬프트용 요약 텍스트를 생성할 수 있습니다.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.db_path = Path(f"data/profiles_{user_id}.db")
        self.init_db()

    def init_db(self):
        """DB 파일 및 user_info 테이블 보장."""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    info TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        logging.debug("user_info table ensured at %s", self.db_path)

    def set_info(self, category: str, key: str, value: str):
        """새 정보를 누적 저장합니다(카테고리/키는 현재 표시용, 스키마 최소화)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_info (user_id, info)
                VALUES (?, ?)
                """,
                (self.user_id, value),
            )
            conn.commit()

    def get_info(self, category: str, key: str) -> str:
        """최신 1개 정보를 조회합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT info FROM user_info
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (self.user_id,),
            )
            result = cursor.fetchone()
            return result[0] if result else ""

    def get_all_info(self) -> list:
        """모든 정보를 오래된 순으로 조회합니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT info, updated_at FROM user_info
                WHERE user_id = ?
                ORDER BY updated_at ASC
                """,
                (self.user_id,),
            )
            return [{"info": row[0], "time": row[1]} for row in cursor.fetchall()]

    def get_all_profile(self):
        """모든 정보를 단순 구조로 반환(프론트 표시용)."""
        all_info = self.get_all_info()
        if all_info:
            return {"personal": {"info_list": [item["info"] for item in all_info]}}
        return {}

    def get_profile_summary(self) -> str:
        """AI 프롬프트에 주입하기 좋은 요약 문장을 생성합니다."""
        all_info = self.get_all_info()
        if all_info:
            info_texts = [item["info"] for item in all_info]
            return f"사용자 정보: {' | '.join(info_texts)}"
        return "사용자 프로필 정보가 없습니다."

    def clear_profile(self):
        """모든 프로필 정보를 삭제합니다."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_info WHERE user_id = ?", (self.user_id,))
            conn.commit()


def get_user_profile(user_id: str = "default") -> UserProfile:
    """팩토리 함수: 사용자별 프로필 인스턴스를 반환합니다."""
    return UserProfile(user_id)
