# 필수 라이브러리 임포트
import os, sys, hashlib, tempfile, shutil, logging # 운영체제, 시스템, 비동기 처리, 해시, 임시파일, 시간 관련 모듈
from fastapi import FastAPI, UploadFile, File, HTTPException  # FastAPI 웹 프레임워크와 파일 업로드, 예외 처리
from fastapi.middleware.cors import CORSMiddleware  # CORS(Cross-Origin Resource Sharing) 미들웨어
from fastapi.responses import JSONResponse  # JSON 응답 생성
from pydantic import BaseModel  # 데이터 검증과 직렬화를 위한 모델
from typing import List, Optional, Dict, Any  # 타입 힌팅을 위한 모듈
import pandas as pd  # 데이터 분석과 조작을 위한 라이브러리

# 로컬 모듈 임포트
from llm_model import load_model  # 대화형 AI 모델 로드 함수
from mcp import ClientSession, StdioServerParameters  # MCP(Model Context Protocol) 클라이언트
from mcp.client.stdio import stdio_client  # 표준 입출력 기반 MCP 클라이언트
from langchain_mcp_adapters.tools import load_mcp_tools  # MCP 도구들을 LangChain 형식으로 로드
from langchain_mcp_adapters.prompts import load_mcp_prompt  # MCP 프롬프트 로드
from langgraph.prebuilt import create_react_agent  # ReAct(Reasoning and Acting) 에이전트 생성
from langchain.tools.retriever import create_retriever_tool  # 문서 검색 도구 생성

# 로컬 모듈들 (RAG 처리와 데이터 처리 관련)
from rag_processsing import *  # RAG(Retrieval-Augmented Generation) 처리 함수들
from data_processing import *  # 데이터 전처리 및 분석 함수들
from conversation_memory import get_memory  # 대화 메모리 관리
from user_profile import get_user_profile  # 사용자 프로필 관리

# 토크나이저 병렬 처리 비활성화 (멀티프로세싱 환경에서 충돌 방지)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="Data Analysis AI Agent API", version="1.0.0")

# CORS(Cross-Origin Resource Sharing) 설정
# 웹 브라우저에서 다른 도메인의 API를 호출할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,  # CORS 미들웨어 추가
    allow_origins=["http://localhost:3000"],  # React 개발 서버 주소 허용
    allow_credentials=True,  # 쿠키, 인증 헤더 등 자격 증명 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 전역 상태 저장소 (메시지는 conversation_memory로 이동)
# 파일 관련 정보만 메모리에 저장
global_state = {
    "retriever": None,  # 문서 검색을 위한 retriever 객체
    "file_hash": None,  # 업로드된 파일의 MD5 해시값 (중복 업로드 체크용)
    "dsid": None,  # 데이터셋 고유 ID
    "meta": None,  # 파일의 메타데이터 정보 (컬럼명, 형태, 확장자 등)
    "preview_df": None,  # 데이터 미리보기 (처음 20행)
    "dtype_df": None  # 각 컬럼의 데이터 타입과 결측치 정보
}

# 대화 메모리 인스턴스 생성
conversation_memory = get_memory()

# 사용자 프로필 인스턴스 생성
user_profile = get_user_profile()

# 애플리케이션 시작시 초기 메시지 확인 및 추가
def ensure_initial_message():
    """초기 메시지가 없으면 추가"""
    recent_messages = conversation_memory.get_recent_messages(limit=1)
    if not recent_messages:
        conversation_memory.add_message(
            "assistant", 
            "안녕하세요! 데이터 분석을 도와드리는 AI 어시스턴트입니다. 파일을 업로드하고 질문해 보세요!"
        )

# 업로드된 파일을 global_state로 복원하는 함수
def restore_uploaded_files():
    """서버 시작 시 기존 업로드된 파일들을 global_state로 복원"""
    try:
        dataset_id, meta = get_latest_uploaded_file()
        if dataset_id and meta:
            # 파일 경로에서 파일 해시 생성
            raw_path = Path(meta["raw_path"])
            if raw_path.exists():
                # 파일 해시 생성
                with open(raw_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                # 데이터 미리보기 생성
                df = pd.read_csv(raw_path, nrows=20)
                
                # 데이터 타입 정보 생성
                dtype_df = pd.DataFrame({
                    "column": df.columns,
                    "null_count": df.isnull().sum().values,
                    "null_ratio": (df.isnull().mean() * 100).round(2).values,
                    "dtype": df.dtypes.astype(str).values,
                })
                
                # Retriever 생성
                retriever = build_retriever_from_path(raw_path)
                
                # global_state 업데이트
                global_state.update({
                    "file_hash": file_hash,
                    "dsid": dataset_id,
                    "meta": meta,
                    "preview_df": df.to_dict('records'),
                    "dtype_df": dtype_df.to_dict('records'),
                    "retriever": retriever
                })
                
                logging.info(f"업로드된 파일 복원 완료: {dataset_id}")
            else:
                logging.warning(f"파일이 존재하지 않음: {raw_path}")
    except Exception as e:
        logging.error(f"파일 복원 중 오류: {str(e)}")

# 초기 메시지 설정
ensure_initial_message()

# 업로드된 파일 복원
restore_uploaded_files()

# 대화형 AI 모델 로드
LLM = load_model.load_llm()  # llm_model 모듈에서 언어 모델을 불러와 LLM 변수에 저장

# MCP 서버 파라미터 설정
# MCP(Model Context Protocol) 서버와 통신하기 위한 설정
SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,  # 현재 Python 인터프리터 경로
    args=["-u", os.path.abspath("MCP/server.py")],  # MCP 서버 실행을 위한 인자들
)

# Pydantic 모델들 - API 요청/응답의 데이터 구조를 정의
# 이 모델들은 자동으로 데이터 검증과 직렬화/역직렬화를 수행

class ChatMessage(BaseModel):
    """개별 채팅 메시지를 나타내는 모델"""
    role: str  # 메시지 발신자 (user: 사용자, assistant: AI)
    content: str  # 메시지 내용

class ChatRequest(BaseModel):
    """채팅 요청을 나타내는 모델"""
    message: str  # 사용자가 보낸 메시지

class ChatResponse(BaseModel):
    """채팅 응답을 나타내는 모델"""
    response: str  # AI의 응답 메시지
    messages: List[ChatMessage]  # 전체 대화 히스토리

class FileUploadResponse(BaseModel):
    """파일 업로드 응답을 나타내는 모델"""
    success: bool  # 업로드 성공 여부
    message: str  # 결과 메시지
    dataset_id: Optional[str] = None  # 생성된 데이터셋 ID (선택적)
    meta: Optional[Dict[str, Any]] = None  # 파일 메타데이터 (선택적)
    preview_df: Optional[List[Dict[str, Any]]] = None  # 데이터 미리보기 (선택적)
    dtype_df: Optional[List[Dict[str, Any]]] = None  # 데이터 타입 정보 (선택적)

class ProfileRequest(BaseModel):
    """프로필 설정 요청을 나타내는 모델"""
    category: str  # 카테고리 ('personal', 'preferences', 'work', 'skills')
    key: str  # 설정할 키
    value: Any  # 설정할 값

class ProfileResponse(BaseModel):
    """프로필 응답을 나타내는 모델"""
    success: bool  # 성공 여부
    message: str  # 결과 메시지
    profile: Optional[Dict[str, Any]] = None  # 프로필 데이터 (선택적)

# API 엔드포인트 정의 시작

@app.get("/")
async def root():
    """루트 엔드포인트 - API가 정상 작동하는지 확인하는 헬스체크 용도"""
    return {"message": "Data Analysis AI Agent API"}  # 간단한 메시지 반환

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), sample_rows: int = 100):
    """파일 업로드 및 처리 엔드포인트"""
    try:
        # 파일 확장자 검증 - 지원하는 형식만 허용
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''  # 파일 확장자 추출
        if ext not in {"csv", "tsv", "txt"}:  # 지원하는 형식 체크
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
        
        # 파일 내용 읽기 및 해시 생성
        file_bytes = await file.read()  # 업로드된 파일의 바이트 데이터 읽기
        file_hash = hashlib.md5(file_bytes).hexdigest()  # MD5 해시 생성 (중복 체크용)
        
        # 임시 파일로 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")  # 임시 파일 생성
        temp_file.write(file_bytes)  # 파일 내용을 임시 파일에 쓰기
        temp_file.close()  # 파일 핸들 닫기
        
        # 파일을 영구 저장소로 이동하고 고유 ID 생성
        dsid, raw_path, ext = save_upload_to_disk_from_path(temp_file.name, file.filename)
        
        try:
            # 파일 구조 분석 (구분자, 인코딩 등 자동 탐지)
            sniff_info = sniff_file(raw_path=raw_path, ext=ext)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"파일 스니핑 오류: {e}")
        
        # 샘플 데이터 로드 (전체 파일이 아닌 일부만 먼저 로드)
        df, sample_info = sample_load(raw_path=raw_path, sniff_info=sniff_info, sample_rows=sample_rows)
        
        # 메타 정보 생성 및 저장
        meta = {
            "sniff": sniff_info,  # 파일 구조 분석 결과
            "shape_sample": list(df.shape),  # 샘플 데이터의 행/열 수
            "shape_total": sample_info.get("shape_total"),  # 전체 데이터의 행/열 수
            "columns": list(df.columns),  # 컬럼명 리스트
            "ext": ext,  # 파일 확장자
            "raw_path": str(raw_path),  # 저장된 파일 경로
        }
        write_meta(dsid, meta)  # 메타데이터를 디스크에 저장
        
        # 데이터 타입 및 결측치 정보 분석
        dtype_df = pd.DataFrame({
            "column": df.columns,  # 컬럼명
            "null_count": df.isnull().sum().values,  # 각 컬럼의 결측치 개수
            "null_ratio": (df.isnull().mean() * 100).round(2).values,  # 결측치 비율 (%)
            "dtype": df.dtypes.astype(str).values,  # 각 컬럼의 데이터 타입
        })
        
        # 문서 검색을 위한 Retriever 생성 (RAG 시스템용)
        retriever = build_retriever_from_path(raw_path)
        
        # 전역 상태에 처리된 데이터 저장
        global_state.update({
            "file_hash": file_hash,  # 파일 해시값 저장
            "dsid": dsid,  # 데이터셋 ID 저장
            "meta": meta,  # 메타데이터 저장
            "preview_df": df.head(20).to_dict('records'),  # 상위 20행을 딕셔너리 리스트로 변환
            "dtype_df": dtype_df.to_dict('records'),  # 데이터타입 정보를 딕셔너리 리스트로 변환
            "retriever": retriever  # 검색기 객체 저장
        })
        
        # 임시 파일 정리
        os.unlink(temp_file.name)  # 더 이상 필요없는 임시 파일 삭제
        
        # 성공 응답 반환
        return FileUploadResponse(
            success=True,  # 성공 상태
            message=f"파일 업로드 성공 - dataset_id: {dsid}",  # 성공 메시지
            dataset_id=dsid,  # 생성된 데이터셋 ID
            meta=meta,  # 파일 메타데이터
            preview_df=df.head(20).to_dict('records'),  # 데이터 미리보기
            dtype_df=dtype_df.to_dict('records')  # 데이터타입 정보
        )
        
    except Exception as e:
        # 오류 발생 시 실패 응답 반환
        return FileUploadResponse(success=False, message=f"업로드 실패: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 메시지 처리 엔드포인트 - 대화 메모리 사용"""
    try:
        # 현재 파일 정보 가져오기
        current_file_info = None
        if global_state.get("meta"):
            current_file_info = {
                "filename": global_state["meta"].get("raw_path", "").split("/")[-1] if global_state["meta"].get("raw_path") else "알 수 없음",
                "columns": global_state["meta"].get("columns", []),
                "shape_total": global_state["meta"].get("shape_total"),
                "ext": global_state["meta"].get("ext", "")
            }
        
        # 사용자 메시지를 파일 컨텍스트와 함께 강화
        enhanced_message = conversation_memory.enhance_message_with_file_context(
            request.message, current_file_info
        )
        
        # 사용자 메시지를 데이터베이스에 저장
        conversation_memory.add_message(
            role="user", 
            content=enhanced_message, 
            file_context=current_file_info
        )
        
        # 최근 대화 히스토리 가져오기
        recent_messages = conversation_memory.get_recent_messages(limit=10)
        
        # MCP Agent를 통해 AI 응답 생성 (대화 히스토리 포함)
        response = await run_agent(enhanced_message, recent_messages)
        
        # AI 응답을 데이터베이스에 저장
        conversation_memory.add_message(
            role="assistant", 
            content=response, 
            file_context=current_file_info
        )
        
        # 최근 메시지들을 API 응답용으로 변환
        recent_messages = conversation_memory.get_recent_messages(limit=50)
        api_messages = [
            ChatMessage(role=msg["role"], content=msg["content"]) 
            for msg in recent_messages
        ]
        
        # 채팅 응답 반환
        return ChatResponse(
            response=response,  # 최신 AI 응답
            messages=api_messages  # 최근 대화 히스토리
        )
        
    except Exception as e:
        # 오류 메시지도 데이터베이스에 저장
        error_response = f"에러가 발생했습니다: {str(e)}"
        conversation_memory.add_message(
            role="assistant", 
            content=error_response
        )
        
        # 최근 메시지들 가져오기
        recent_messages = conversation_memory.get_recent_messages(limit=50)
        api_messages = [
            ChatMessage(role=msg["role"], content=msg["content"]) 
            for msg in recent_messages
        ]
        
        # 에러 응답 반환
        return ChatResponse(
            response=error_response,
            messages=api_messages
        )

@app.get("/messages")
async def get_messages():
    """채팅 메시지 히스토리 조회 엔드포인트 - 데이터베이스에서 조회"""
    recent_messages = conversation_memory.get_recent_messages(limit=100)
    api_messages = [
        {"role": msg["role"], "content": msg["content"]} 
        for msg in recent_messages
    ]
    return {"messages": api_messages}  # 최근 대화 히스토리 반환

@app.get("/file-info")
async def get_file_info():
    """업로드된 파일 정보 조회 엔드포인트"""
    # 업로드된 파일이 있는지 확인
    if not global_state.get("meta"):
        raise HTTPException(status_code=404, detail="업로드된 파일이 없습니다.")
    
    # 파일 정보 반환
    return {
        "dataset_id": global_state["dsid"],  # 데이터셋 ID
        "meta": global_state["meta"],  # 파일 메타데이터
        "preview_df": global_state["preview_df"],  # 데이터 미리보기
        "dtype_df": global_state["dtype_df"]  # 데이터타입 정보
    }

@app.delete("/clear-data")
async def clear_all_data():
    """모든 데이터 파일과 상태 초기화 엔드포인트"""
    try:
        BASE_DIR = Path(__file__).resolve().parent / "data/"
        print(BASE_DIR)
        meta_path = BASE_DIR / "meta/"
        uploads_path = BASE_DIR / "uploads/"
        if os.path.exists(meta_path) or os.path.exists(uploads_path):
            
            shutil.rmtree(meta_path)
            shutil.rmtree(uploads_path)
            
            # 전역 상태 초기화 (파일 관련 정보만)
            global_state.update({
                "retriever": None,
                "file_hash": None,
                "dsid": None,
                "meta": None,
                "preview_df": None,
                "dtype_df": None
            })
            
            # 대화 메모리 초기화
            conversation_memory.clear_conversation()
            # 초기 메시지 추가
            conversation_memory.add_message(
                "assistant", 
                "데이터가 초기화되었습니다. 새로운 파일을 업로드해 주세요!"
            )
            return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "모든 데이터가 성공적으로 초기화되었습니다.",
            }
        ) 
        else:
            return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "데이터 파일이 비어있습니다.",
            }
        ) 
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"데이터 초기화 실패: {str(e)}"
            }
        )

# 프로필 관리 API 엔드포인트들
@app.post("/profile", response_model=ProfileResponse)
async def set_profile(request: ProfileRequest):
    """사용자 프로필 정보 설정"""
    try:
        user_profile.set_info(request.category, request.key, request.value)
        return ProfileResponse(
            success=True,
            message=f"{request.category}.{request.key} 정보가 저장되었습니다."
        )
    except Exception as e:
        return ProfileResponse(
            success=False,
            message=f"프로필 저장 실패: {str(e)}"
        )

@app.get("/profile", response_model=ProfileResponse)
async def get_profile():
    """사용자의 전체 프로필 조회"""
    try:
        profile = user_profile.get_all_profile()
        return ProfileResponse(
            success=True,
            message="프로필 조회 성공",
            profile=profile
        )
    except Exception as e:
        return ProfileResponse(
            success=False,
            message=f"프로필 조회 실패: {str(e)}"
        )

async def run_agent(user_input: str, conversation_history: List[Dict[str, Any]] = None):
    """데이터 분석을 도와주는 AI 에이전트 실행 함수 (대화 히스토리 포함)"""
    try:
        # MCP 서버와 연결 설정 및 세션 생성
        async with stdio_client(SERVER_PARAMS) as (read, write):  # 표준 입출력 기반 클라이언트 생성
            async with ClientSession(read, write) as session:  # MCP 세션 생성
                await session.initialize()  # 세션 초기화
                
                # MCP 도구들 로드 및 리스트로 변환
                try:
                    mcp_tools = await load_mcp_tools(session)  # 사용 가능한 도구들 로드
                    tools = list(mcp_tools)  # 도구 리스트로 변환
                except Exception as e:
                    print(f"Warning: Failed to load MCP tools: {e}")
                    tools = []

                # 업로드된 파일이 있으면 문서 검색 도구 추가
                if global_state.get("retriever"):
                    try:
                        retriever_tool = create_retriever_tool(
                            global_state["retriever"],  # 기존에 생성된 retriever 객체 사용
                            name="doc_search",  # 도구 이름
                            description=(  # 도구 설명 (에이전트가 언제 사용할지 결정하는 기준)
                                "업로드된 문서에서 질문과 관련된 내용을 찾습니다. "
                                "요약/개요/핵심 정리 등도 이 도구로 필요한 근거를 수집한 후 작성하세요."
                            ),
                        )
                        tools.append(retriever_tool)  # 문서 검색 도구를 도구 리스트에 추가
                    except Exception as e:
                        print(f"Warning: Failed to add retriever tool: {e}")

                # ReAct 에이전트 생성 (사고하고 행동하는 에이전트)
                agent = create_react_agent(LLM, tools)  # 언어모델과 도구들로 에이전트 생성
                
                # 대화 히스토리를 포함한 메시지 구성
                messages = []
                
                # 사용자 프로필 정보 추가
                try:
                    profile_summary = user_profile.get_profile_summary()
                    if profile_summary != "사용자 프로필 정보가 없습니다.":
                        messages.append({
                            "role": "system", 
                            "content": f"사용자 프로필 정보:\n{profile_summary}\n\n위 정보를 바탕으로 개인화된 답변을 제공해주세요."
                        })
                except Exception as e:
                    print(f"Warning: Failed to get profile summary: {e}")
                
                # 업로드된 파일 정보가 있으면 시스템 메시지로 추가
                if global_state.get("meta"):
                    file_info = global_state["meta"]
                    messages.append({
                        "role": "system",
                        "content": f"""현재 업로드된 파일 정보:
                                    - 파일명: {file_info.get('raw_path', '').split('/')[-1] if file_info.get('raw_path') else '알 수 없음'}
                                    - 형식: {file_info.get('ext', '알 수 없음')}
                                    - 컬럼: {', '.join(file_info.get('columns', []))}
                                    - 전체 데이터 크기: {file_info.get('shape_total', '알 수 없음')}

                                    사용자가 파일에 대해 질문하면 doc_search 도구를 사용하여 파일 내용을 검색하고 분석해주세요."""
                    })

                # 이전 대화가 있으면 추가 (최근 5개만, 토큰 절약)
                if conversation_history:
                    messages.append({
                        "role": "system", 
                        "content": "이전 대화 내용을 참고하여 맥락을 이해하고 답변해주세요."
                    })
                    
                    # 최근 대화만 추가 (너무 많으면 토큰 초과)
                    for msg in conversation_history[-5:]:  # 최근 5개만
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # 현재 사용자 메시지 추가
                messages.append({
                    "role": "user",
                    "content": user_input
                })
                
                # 에이전트 실행 및 응답 추출
                response = await agent.ainvoke({"messages": messages})  # 대화 히스토리 포함하여 호출
                answer = response["messages"][-1].content  # 응답 메시지에서 마지막 내용 추출
                return answer  # AI의 최종 응답 반환
                
    except Exception as e:
        print(f"Error in run_agent: {e}")
        return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"

def save_upload_to_disk_from_path(file_path: str, filename: str) -> tuple[str, Path, str]:
    """임시 파일을 영구 저장소로 이동하여 저장하는 함수"""
    ext = Path(filename).suffix.lower().lstrip(".")  # 파일 확장자 추출 (대소문자 변환, '.' 제거)
    dsid = gen_dataset_id(filename)  # 파일명을 기반으로 고유 데이터셋 ID 생성
    target_dir = UPLOAD_DIR / dsid  # 데이터셋별 디렉토리 경로 생성
    target_dir.mkdir(parents=True, exist_ok=True)  # 디렉토리 생성 (상위 디렉토리도 함께 생성)
    raw_path = target_dir / f"raw.{ext if ext else 'bin'}"  # 원본 파일 저장 경로
    
    # 임시 파일을 영구 저장소로 복사
    import shutil  # 파일 조작을 위한 라이브러리
    shutil.copy2(file_path, raw_path)  # 원본 파일과 메타데이터를 모두 복사
    
    return dsid, raw_path, ext  # 데이터셋 ID, 저장 경로, 확장자 반환

def build_retriever_from_path(file_path: Path, k: int = 3):
    """업로드된 파일로부터 문서 검색용 Retriever 객체를 생성하는 함수"""
    df = pd.read_csv(file_path)  # CSV 파일을 데이터프레임으로 로드
    
    # 각 행을 개별 문서로 변환
    docs = []  # 문서 리스트 초기화
    for i, row in df.iterrows():  # 데이터프레임의 각 행에 대해 반복
        content = row.to_json(force_ascii=False)  # 행 데이터를 JSON 문자열로 변환 (한글 지원)
        docs.append(Document(page_content=content, metadata={"row": i}))  # 문서 객체 생성 및 리스트에 추가
    
    # 한국어 지원 임베딩 모델 로드
    embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # FAISS 벡터 데이터베이스 생성 (빠른 유사도 검색용)
    vs = FAISS.from_documents(docs, embed)  # 문서들을 벡터화하여 데이터베이스에 저장
    
    # 검색기 객체 생성 및 반환 (k개의 최유사 문서 반환)
    return vs.as_retriever(search_kwargs={"k": k})

# 메인 실행 부분 - 직접 실행할 때만 작동
if __name__ == "__main__":
    import uvicorn  # ASGI 서버 (FastAPI 실행용)
    # FastAPI 애플리케이션을 모든 인터페이스의 8000번 포트에서 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
