from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.mongodb import get_database
from typing import List
from datetime import datetime, timezone, timedelta

router = APIRouter()

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def convert_utc_to_ist(utc_datetime: datetime) -> str:
    """Convert UTC datetime to IST string"""
    if utc_datetime.tzinfo is None:
        # Assume UTC if no timezone info
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    ist_datetime = utc_datetime.astimezone(IST)
    return ist_datetime.isoformat()

@router.get("/history")
async def get_user_history(candidate_id: str = Query(..., alias="user_id"), db=Depends(get_database)):
    try:
        history_cursor = db["history"].find({"user_id": candidate_id}).sort("timestamp", -1)
        history = list(history_cursor)
        for h in history:
            h["_id"] = str(h["_id"])  # Convert ObjectId to string for JSON serialization
            # Convert timestamp to IST
            if h.get("timestamp"):
                h["timestamp"] = convert_utc_to_ist(h["timestamp"])
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
