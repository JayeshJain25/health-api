from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.auth import register_user, login_user

router = APIRouter()

class UserRegister(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(user: UserRegister):
    try:
        await register_user(user.email, user.name, user.password)
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    try:
        token, user_id = await login_user(user.email, user.password)
        return {"access_token": token, "user_id": user_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))