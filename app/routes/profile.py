from fastapi import APIRouter, HTTPException
from app.schemas.profile import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.services.profile import create_user_profile, get_user_profile, update_user_profile

router = APIRouter()

@router.post("/profile", response_model=dict)
async def create_profile(
    profile: UserProfileCreate,
    user_id: str
):
    """Create or update user profile information"""
    try:
        profile_id = await create_user_profile(
            user_id=user_id,
            gender=profile.gender,
            date_of_birth=profile.date_of_birth,
            height=profile.height,
            weight=profile.weight,
            goal=profile.goal
        )
        return {"message": "Profile created successfully", "profile_id": profile_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str):
    """Get user profile information"""
    try:
        profile = await get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/profile", response_model=dict)
async def update_profile(
    profile: UserProfileCreate,
    user_id: str
):
    """Update user profile information"""
    try:
        success = await update_user_profile(
            user_id=user_id,
            gender=profile.gender,
            date_of_birth=profile.date_of_birth,
            height=profile.height,
            weight=profile.weight,
            goal=profile.goal
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
