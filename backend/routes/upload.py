import hashlib
import os
import tempfile
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.schemas.file import FileUploadResponse
from backend.services.ingest import save_upload_to_disk_from_path
from backend.state import global_state
from core.data_processing.sniff import sniff_file
from core.data_processing.load import sample_load
from core.data_processing.meta import write_meta
from core.rag.builder import build_retriever_from_csv


router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), sample_rows: int = 100):
    try:
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in {"csv", "tsv", "txt"}:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

        file_bytes = await file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        temp_file.write(file_bytes)
        temp_file.close()

        dsid, raw_path, ext = save_upload_to_disk_from_path(temp_file.name, file.filename)

        try:
            sniff_info = sniff_file(raw_path=raw_path, ext=ext)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"파일 스니핑 오류: {e}")

        df, sample_info = sample_load(raw_path=raw_path, sniff_info=sniff_info, sample_rows=sample_rows)

        meta: Dict[str, Any] = {
            "sniff": sniff_info,
            "shape_sample": list(df.shape),
            "shape_total": sample_info.get("shape_total"),
            "columns": list(df.columns),
            "ext": ext,
            "raw_path": str(raw_path),
        }
        write_meta(dsid, meta)

        dtype_df = pd.DataFrame(
            {
                "column": df.columns,
                "null_count": df.isnull().sum().values,
                "null_ratio": (df.isnull().mean() * 100).round(2).values,
                "dtype": df.dtypes.astype(str).values,
            }
        )

        retriever = build_retriever_from_csv(raw_path)

        global_state.update(
            {
                "file_hash": file_hash,
                "dsid": dsid,
                "meta": meta,
                "preview_df": df.head(20).to_dict("records"),
                "dtype_df": dtype_df.to_dict("records"),
                "retriever": retriever,
            }
        )

        os.unlink(temp_file.name)

        return FileUploadResponse(
            success=True,
            message=f"파일 업로드 성공 - dataset_id: {dsid}",
            dataset_id=dsid,
            meta=meta,
            preview_df=df.head(20).to_dict("records"),
            dtype_df=dtype_df.to_dict("records"),
        )

    except Exception as e:
        return FileUploadResponse(success=False, message=f"업로드 실패: {str(e)}")
