from typing import Any, Dict, Optional
from pydantic import BaseModel


class ProfileRequest(BaseModel):
    category: str
    key: str
    value: Any


class ProfileResponse(BaseModel):
    success: bool
    message: str
    profile: Optional[Dict[str, Any]] = None

