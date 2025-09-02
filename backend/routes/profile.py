from fastapi import APIRouter

from backend.schemas.profile import ProfileRequest, ProfileResponse
from backend.state import user_profile


router = APIRouter()


@router.post("/profile", response_model=ProfileResponse)
async def set_profile(request: ProfileRequest):
    try:
        user_profile.set_info(request.category, request.key, request.value)
        return ProfileResponse(success=True, message="프로필 정보가 저장되었습니다.")
    except Exception as e:
        return ProfileResponse(success=False, message=f"프로필 저장 실패: {str(e)}")


@router.get("/profile", response_model=ProfileResponse)
async def get_profile():
    try:
        profile = user_profile.get_all_profile()
        return ProfileResponse(success=True, message="프로필 조회 성공", profile=profile)
    except Exception as e:
        return ProfileResponse(success=False, message=f"프로필 조회 실패: {str(e)}")

