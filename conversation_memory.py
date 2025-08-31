# SQLite를 사용한 데이터베이스 조작을 위한 라이브러리
import sqlite3
# JSON 데이터 직렬화/역직렬화를 위한 라이브러리
import json
# 타입 힌팅을 위한 라이브러리들
from typing import List, Dict, Any, Optional
# 파일 경로 조작을 위한 pathlib 라이브러리
from pathlib import Path

class ConversationMemory:
    """
    대화 메모리 관리 클래스
    - 사용자와 AI 간의 대화 내용을 SQLite 데이터베이스에 저장하고 관리
    - 단일 사용자부터 시작해서 다중 사용자로 확장 가능한 구조
    - 파일 컨텍스트 정보도 함께 저장하여 파일 관련 대화의 맥락 유지
    """
    
    def __init__(self, user_id: str = "default"):
        """
        ConversationMemory 인스턴스 초기화
        
        Args:
            user_id (str): 사용자 식별자, 기본값은 "default"
                          향후 다중 사용자 지원 시 각 사용자별로 구분하기 위함
        """
        self.user_id = user_id
        # 사용자별로 별도의 데이터베이스 파일 생성 (data/conversations_{user_id}.db)
        self.db_path = Path(f"data/conversations_{user_id}.db")
        # 데이터베이스 초기화 실행
        self.init_db()
    
    def init_db(self):
        """
        데이터베이스 초기화 및 테이블 생성
        - data 디렉토리가 없으면 생성
        - conversations 테이블이 없으면 생성
        """
        # 데이터 디렉토리가 없으면 생성 (exist_ok=True로 이미 존재해도 에러 없음)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # SQLite 연결 및 테이블 생성 (with문으로 자동 연결 해제)
        with sqlite3.connect(self.db_path) as conn:
            # conversations 테이블 생성 (없을 경우에만)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 자동 증가 기본키
                    user_id TEXT NOT NULL,                 -- 사용자 식별자
                    role TEXT NOT NULL,                    -- 메시지 역할 (user, assistant, system 등)
                    content TEXT NOT NULL,                 -- 메시지 내용
                    file_context TEXT,                     -- 파일 컨텍스트 정보 (JSON 문자열로 저장)
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP  -- 메시지 생성 시간 (자동)
                )
            """)
            
            # 테이블 존재 확인 및 검증
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='conversations'
            """)
            if cursor.fetchone():
                print(f"✓ conversations 테이블 초기화 완료: {self.db_path}")
            else:
                print(f"✗ conversations 테이블 생성 실패: {self.db_path}")
            
            conn.commit()  # 변경사항 커밋
    
    def add_message(self, role: str, content: str, file_context: Optional[Dict[str, Any]] = None):
        """
        메시지를 데이터베이스에 저장
        
        Args:
            role (str): 메시지 역할 ('user', 'assistant', 'system' 등)
            content (str): 메시지 내용
            file_context (Optional[Dict[str, Any]]): 파일 관련 컨텍스트 정보 (선택사항)
                - filename: 파일명
                - columns: 데이터프레임 컬럼 정보
                - shape_total: 데이터 크기 등
        """
        # 파일 컨텍스트가 있으면 JSON 문자열로 변환, 없으면 None
        file_context_json = json.dumps(file_context, ensure_ascii=False) if file_context else None
        
        # 데이터베이스에 메시지 삽입
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations (user_id, role, content, file_context)
                VALUES (?, ?, ?, ?)
            """, (self.user_id, role, content, file_context_json))
            conn.commit()
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        최근 N개의 메시지를 시간순으로 반환 (토큰 절약을 위해 제한)
        
        Args:
            limit (int): 반환할 메시지 개수, 기본값 20개
            
        Returns:
            List[Dict[str, Any]]: 메시지 리스트, 각 메시지는 role, content, file_context, timestamp 포함
        """
        with sqlite3.connect(self.db_path) as conn:
            # Row 팩토리 설정으로 딕셔너리 형태로 결과 받기
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT role, content, file_context, timestamp
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC  -- 최신순 정렬
                LIMIT ?
            """, (self.user_id, limit))
            
            messages = []
            # fetchall() 결과를 역순으로 정렬하여 시간순(오래된 것부터)으로 만듦
            for row in reversed(cursor.fetchall()):
                # JSON 문자열이 있으면 파싱, 없으면 None
                file_context = json.loads(row['file_context']) if row['file_context'] else None
                messages.append({
                    "role": row['role'],
                    "content": row['content'],
                    "file_context": file_context,
                    "timestamp": row['timestamp']
                })
            return messages
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        모든 메시지를 시간순으로 반환 (전체 대화 기록이 필요한 경우 사용)
        
        Returns:
            List[Dict[str, Any]]: 전체 메시지 리스트
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT role, content, file_context, timestamp
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp ASC  -- 시간순 정렬 (오래된 것부터)
            """, (self.user_id,))
            
            messages = []
            for row in cursor.fetchall():
                file_context = json.loads(row['file_context']) if row['file_context'] else None
                messages.append({
                    "role": row['role'],
                    "content": row['content'],
                    "file_context": file_context,
                    "timestamp": row['timestamp']
                })
            return messages
    
    def enhance_message_with_file_context(self, message: str, current_file_info: Optional[Dict[str, Any]]) -> str:
        """
        메시지에서 파일 참조 표현을 실제 파일명으로 자동 변환
        - 사용자가 "내가 올린 파일"이라고 하면 실제 파일명으로 바꿔줌
        
        Args:
            message (str): 원본 메시지
            current_file_info (Optional[Dict[str, Any]]): 현재 파일 정보
            
        Returns:
            str: 파일명이 구체화된 메시지
        """
        # 파일 정보가 없으면 원본 메시지 그대로 반환
        if not current_file_info:
            return message
        
        # 사용자가 자주 사용하는 파일 참조 표현들
        file_references = [
            "내가 올린 파일", "업로드한 파일", "올린 파일", "이 파일",
            "현재 파일", "업로드된 파일"
        ]
        
        enhanced_message = message
        # 파일 정보에서 파일명 추출 (없으면 'unknown')
        filename = current_file_info.get('filename', 'unknown')
        
        # 각 파일 참조 표현을 실제 파일명으로 치환
        for ref in file_references:
            if ref in message:
                enhanced_message = enhanced_message.replace(
                    ref, 
                    f"{filename} 파일"
                )
        
        return enhanced_message
    
    def get_file_aware_context(self, current_file_info: Optional[Dict[str, Any]]) -> str:
        """
        현재 파일 정보를 포함한 컨텍스트 문자열 생성
        - AI에게 현재 어떤 파일을 다루고 있는지 알려주기 위한 컨텍스트
        
        Args:
            current_file_info (Optional[Dict[str, Any]]): 현재 파일 정보
            
        Returns:
            str: 파일 컨텍스트를 포함한 설명 문자열
        """
        # 파일 정보가 없으면 안내 메시지 반환
        if not current_file_info:
            return "현재 업로드된 파일이 없습니다."
        
        # 파일명을 포함한 기본 컨텍스트
        context_parts = [f"현재 분석 중인 파일: {current_file_info.get('filename', '알 수 없음')}"]
        
        # 데이터프레임의 컬럼 정보가 있으면 추가 (처음 5개만 표시)
        if 'columns' in current_file_info:
            context_parts.append(f"컬럼: {', '.join(current_file_info['columns'][:5])}...")
        
        # 데이터 크기 정보가 있으면 추가
        if 'shape_total' in current_file_info:
            shape = current_file_info['shape_total']
            if shape:
                context_parts.append(f"크기: {shape[0]}행 x {shape[1]}열")
        
        # 각 정보를 " | "로 연결하여 반환
        return " | ".join(context_parts)
    
    def clear_conversation(self):
        """
        현재 사용자의 대화 기록을 모두 삭제
        - 새로 시작하거나 개인정보 보호를 위해 기록을 지울 때 사용
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations WHERE user_id = ?", (self.user_id,))
            conn.commit()

# 전역 메모리 인스턴스 생성 (기본 사용자용)
# 나중에 팩토리 패턴이나 싱글톤 패턴으로 확장 가능
memory = ConversationMemory()

def get_memory(user_id: str = "default") -> ConversationMemory:
    """
    메모리 인스턴스를 가져오는 팩토리 함수
    - 현재는 단순하게 새 인스턴스를 반환하지만, 향후 다중 사용자 지원 시 확장
    - 사용자별 메모리 인스턴스를 캐싱하거나 풀링하는 기능 추가 가능
    
    Args:
        user_id (str): 사용자 식별자
        
    Returns:
        ConversationMemory: 해당 사용자의 메모리 인스턴스
    """
    # 향후 개선사항: 사용자별 인스턴스 캐싱, 메모리 풀 관리 등
    return ConversationMemory(user_id)