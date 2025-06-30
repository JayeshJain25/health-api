from datetime import date, datetime
from app.database.mongodb import MongoDB
from typing import Optional, Dict, Any
from bson import ObjectId

async def create_user_profile(
    user_id: str,
    gender: str,
    date_of_birth: date,
    height: float,
    weight: float,
    goal: str
) -> str:
    """Create a new user profile or update existing one"""
    db = MongoDB()
    try:
        profiles = db.get_collection("user_profiles")
        users = db.get_collection("users")
        
        # Verify user exists
        user = users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise Exception("User not found")
        
        user_email = user["email"]
        
        # Check if profile already exists
        existing_profile = profiles.find_one({"user_id": user_id})
        
        profile_data = {
            "user_id": user_id,
            "user_email": user_email,
            "gender": gender.lower(),
            "date_of_birth": date_of_birth.isoformat(),
            "height": height,
            "weight": weight,
            "goal": goal.lower(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if existing_profile:
            # Update existing profile
            profiles.update_one(
                {"user_id": user_id},
                {"$set": profile_data}
            )
            profile_id = str(existing_profile["_id"])
        else:
            # Create new profile
            profile_data["created_at"] = datetime.utcnow().isoformat()
            result = profiles.insert_one(profile_data)
            profile_id = str(result.inserted_id)
        
        return profile_id
    finally:
        db.close()

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by user_id"""
    db = MongoDB()
    try:
        profiles = db.get_collection("user_profiles")
        
        # Get profile directly by user_id
        profile = profiles.find_one({"user_id": user_id})
        if not profile:
            return None
        
        # Convert ObjectId to string and format response
        profile_response = {
            "user_id": profile["user_id"],
            "gender": profile["gender"],
            "date_of_birth": profile["date_of_birth"],
            "height": profile["height"],
            "weight": profile["weight"],
            "goal": profile["goal"],
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at")
        }
        
        return profile_response
    finally:
        db.close()

async def update_user_profile(
    user_id: str,
    gender: str,
    date_of_birth: date,
    height: float,
    weight: float,
    goal: str
) -> bool:
    """Update user profile"""
    db = MongoDB()
    try:
        profiles = db.get_collection("user_profiles")
        
        # Update profile directly by user_id
        update_data = {
            "gender": gender.lower(),
            "date_of_birth": date_of_birth.isoformat(),
            "height": height,
            "weight": weight,
            "goal": goal.lower(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = profiles.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    finally:
        db.close()

async def get_user_profile_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by user_id (helper function for internal use)"""
    db = MongoDB()
    try:
        profiles = db.get_collection("user_profiles")
        
        profile = profiles.find_one({"user_id": user_id})
        if not profile:
            return None
        
        profile_response = {
            "user_id": profile["user_id"],
            "gender": profile["gender"],
            "date_of_birth": profile["date_of_birth"],
            "height": profile["height"],
            "weight": profile["weight"],
            "goal": profile["goal"],
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at")
        }
        
        return profile_response
    finally:
        db.close()
