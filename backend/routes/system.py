import os
import shutil
from fastapi import APIRouter, HTTPException

from backend.state import conversation_memory, global_state
from config.paths import META_DIR, UPLOAD_DIR


router = APIRouter()


@router.get("/file-info")
async def get_file_info():
    if not global_state.get("meta"):
        raise HTTPException(status_code=404, detail="업로드된 파일이 없습니다.")
    return {
        "dataset_id": global_state["dsid"],
        "meta": global_state["meta"],
        "preview_df": global_state["preview_df"],
        "dtype_df": global_state["dtype_df"],
    }


@router.delete("/clear-data")
async def clear_all_data():
    try:
        if META_DIR.exists():
            shutil.rmtree(META_DIR)
        if UPLOAD_DIR.exists():
            shutil.rmtree(UPLOAD_DIR)

        META_DIR.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        global_state.update(
            {
                "retriever": None,
                "file_hash": None,
                "dsid": None,
                "meta": None,
                "preview_df": None,
                "dtype_df": None,
            }
        )

        conversation_memory.clear_conversation()
        return {"success": True, "message": "모든 데이터가 초기화되었습니다."}
    except Exception as e:
        return {"success": False, "message": f"데이터 초기화 실패: {e}"}

