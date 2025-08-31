# 사용자 프로필 관리 모듈
import sqlite3
from pathlib import Path

class UserProfile:
    """간단한 사용자 정보 저장"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.db_path = Path(f"data/profiles_{user_id}.db")
        self.init_db()
    
    def init_db(self):
        """데이터베이스 초기화"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # user_info 테이블 생성 (없을 경우에만)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    info TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 테이블 존재 확인 및 검증
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_info'
            """)
            if cursor.fetchone():
                print(f"✓ user_info 테이블 초기화 완료: {self.db_path}")
            else:
                print(f"✗ user_info 테이블 생성 실패: {self.db_path}")
            
            conn.commit()
    
    def set_info(self, category: str, key: str, value: str):
        """정보 저장 (누적)"""
        with sqlite3.connect(self.db_path) as conn:
            # 새 정보 추가 (기존 정보 유지)
            conn.execute("""
                INSERT INTO user_info (user_id, info)
                VALUES (?, ?)
            """, (self.user_id, value))
            conn.commit()
    
    def get_info(self, category: str, key: str) -> str:
        """최신 정보 하나만 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT info FROM user_info
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (self.user_id,))
            
            result = cursor.fetchone()
            return result[0] if result else ""
    
    def get_all_info(self) -> list:
        """모든 정보 조회 (시간순)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT info, updated_at FROM user_info
                WHERE user_id = ?
                ORDER BY updated_at ASC
            """, (self.user_id,))
            
            return [{"info": row[0], "time": row[1]} for row in cursor.fetchall()]
    
    def get_all_profile(self):
        """전체 프로필 조회 (모든 정보 포함)"""
        all_info = self.get_all_info()
        if all_info:
            return {"personal": {"info_list": [item["info"] for item in all_info]}}
        return {}
    
    def get_profile_summary(self) -> str:
        """AI가 사용할 프로필 요약 (모든 정보 포함)"""
        all_info = self.get_all_info()
        if all_info:
            info_texts = [item["info"] for item in all_info]
            return f"사용자 정보: {' | '.join(info_texts)}"
        return "사용자 프로필 정보가 없습니다."
    
    def clear_profile(self):
        """프로필 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_info WHERE user_id = ?", (self.user_id,))
            conn.commit()

def get_user_profile(user_id: str = "default") -> UserProfile:
    return UserProfile(user_id)