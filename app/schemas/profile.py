from pydantic import BaseModel, validator
from datetime import date
from typing import Optional

class UserProfileCreate(BaseModel):
    gender: str
    date_of_birth: date
    height: float  # in cm
    weight: float  # in kg
    goal: str
    
    @validator('gender')
    def validate_gender(cls, v):
        allowed_genders = ['male', 'female', 'other']
        if v.lower() not in allowed_genders:
            raise ValueError(f'Gender must be one of: {", ".join(allowed_genders)}')
        return v.lower()
    
    @validator('goal')
    def validate_goal(cls, v):
        allowed_goals = ['lose_weight', 'build_muscle', 'stay_fit']
        if v.lower() not in allowed_goals:
            raise ValueError(f'Goal must be one of: {", ".join(allowed_goals)}')
        return v.lower()
    
    @validator('height')
    def validate_height(cls, v):
        if v <= 0 or v > 300:  # reasonable height range in cm
            raise ValueError('Height must be between 1 and 300 cm')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v <= 0 or v > 1000:  # reasonable weight range in kg
            raise ValueError('Weight must be between 1 and 1000 kg')
        return v

class UserProfileResponse(BaseModel):
    user_id: str
    gender: str
    date_of_birth: str  # ISO format string
    height: float
    weight: float
    goal: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserProfileUpdate(BaseModel):
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            allowed_genders = ['male', 'female', 'other']
            if v.lower() not in allowed_genders:
                raise ValueError(f'Gender must be one of: {", ".join(allowed_genders)}')
            return v.lower()
        return v
    
    @validator('goal')
    def validate_goal(cls, v):
        if v is not None:
            allowed_goals = ['lose_weight', 'build_muscle', 'stay_fit']
            if v.lower() not in allowed_goals:
                raise ValueError(f'Goal must be one of: {", ".join(allowed_goals)}')
            return v.lower()
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v is not None and (v <= 0 or v > 300):
            raise ValueError('Height must be between 1 and 300 cm')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and (v <= 0 or v > 1000):
            raise ValueError('Weight must be between 1 and 1000 kg')
        return v
