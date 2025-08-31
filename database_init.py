"""
데이터베이스 테이블 초기화 모듈
- 프로젝트에서 사용하는 모든 데이터베이스 테이블들이 존재하는지 확인하고 없으면 생성
- 앱 시작 시 한 번 실행하여 데이터베이스 스키마 일관성 보장
"""
import sqlite3
from pathlib import Path
from typing import Optional


def ensure_data_directory():
    """data 디렉토리가 없으면 생성"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def init_conversation_tables(user_id: str = "default"):
    """대화 메모리 테이블 초기화"""
    data_dir = ensure_data_directory()
    db_path = data_dir / f"conversations_{user_id}.db"
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                file_context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    print(f"✓ 대화 메모리 테이블 초기화 완료: {db_path}")


def init_profile_tables(user_id: str = "default"):
    """사용자 프로필 테이블 초기화"""
    data_dir = ensure_data_directory()
    db_path = data_dir / f"profiles_{user_id}.db"
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                info TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    print(f"✓ 사용자 프로필 테이블 초기화 완료: {db_path}")


def init_all_tables(user_ids: Optional[list] = None):
    """
    모든 데이터베이스 테이블 초기화
    
    Args:
        user_ids: 초기화할 사용자 ID 리스트. None이면 기본 사용자만 초기화
    """
    if user_ids is None:
        user_ids = ["default"]
    
    print("데이터베이스 테이블 초기화 시작...")
    
    for user_id in user_ids:
        try:
            init_conversation_tables(user_id)
            init_profile_tables(user_id)
        except Exception as e:
            print(f"✗ 사용자 '{user_id}' 테이블 초기화 실패: {e}")
    
    print("데이터베이스 테이블 초기화 완료!")


def verify_all_tables(user_ids: Optional[list] = None):
    """
    모든 데이터베이스 테이블이 존재하는지 검증
    
    Args:
        user_ids: 검증할 사용자 ID 리스트
    
    Returns:
        bool: 모든 테이블이 존재하면 True
    """
    if user_ids is None:
        user_ids = ["default"]
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("✗ data 디렉토리가 존재하지 않습니다.")
        return False
    
    success = True
    
    for user_id in user_ids:
        # 대화 메모리 테이블 확인
        conv_db_path = data_dir / f"conversations_{user_id}.db"
        if conv_db_path.exists():
            try:
                with sqlite3.connect(conv_db_path) as conn:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='conversations'
                    """)
                    if cursor.fetchone():
                        print(f"✓ conversations 테이블 존재: {user_id}")
                    else:
                        print(f"✗ conversations 테이블 없음: {user_id}")
                        success = False
            except Exception as e:
                print(f"✗ conversations 테이블 확인 실패 ({user_id}): {e}")
                success = False
        else:
            print(f"✗ conversations 데이터베이스 파일 없음: {user_id}")
            success = False
        
        # 프로필 테이블 확인
        profile_db_path = data_dir / f"profiles_{user_id}.db"
        if profile_db_path.exists():
            try:
                with sqlite3.connect(profile_db_path) as conn:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='user_info'
                    """)
                    if cursor.fetchone():
                        print(f"✓ user_info 테이블 존재: {user_id}")
                    else:
                        print(f"✗ user_info 테이블 없음: {user_id}")
                        success = False
            except Exception as e:
                print(f"✗ user_info 테이블 확인 실패 ({user_id}): {e}")
                success = False
        else:
            print(f"✗ profiles 데이터베이스 파일 없음: {user_id}")
            success = False
    
    return success


if __name__ == "__main__":
    # 스크립트 직접 실행 시 테이블 초기화 및 검증
    print("=" * 50)
    print("데이터베이스 테이블 초기화 및 검증")
    print("=" * 50)
    
    # 모든 테이블 초기화
    init_all_tables()
    
    print("\n" + "-" * 50)
    print("테이블 존재 여부 검증")
    print("-" * 50)
    
    # 테이블 존재 여부 검증
    if verify_all_tables():
        print("\n🎉 모든 테이블이 정상적으로 존재합니다!")
    else:
        print("\n⚠️ 일부 테이블이 누락되었습니다.")