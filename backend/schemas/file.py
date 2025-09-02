from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    success: bool
    message: str
    dataset_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    preview_df: Optional[List[Dict[str, Any]]] = None
    dtype_df: Optional[List[Dict[str, Any]]] = None

