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
        token, user_id = await register_user(user.email, user.name, user.password)
        return {"message": "User registered successfully", "access_token": token, "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    try:
        token, user_id, user_name = await login_user(user.email, user.password)
        return {"access_token": token, "user_id": user_id, "name": user_name, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))