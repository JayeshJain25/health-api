from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.mongodb import get_database
from typing import List

router = APIRouter()

@router.get("/history")
async def get_user_history(candidate_id: str = Query(..., alias="user_id"), db=Depends(get_database)):
    try:
        history_cursor = db["history"].find({"user_id": candidate_id}).sort("timestamp", -1)
        history = list(history_cursor)
        for h in history:
            h["_id"] = str(h["_id"])  # Convert ObjectId to string for JSON serialization
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
