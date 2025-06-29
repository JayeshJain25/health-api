from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import os
from google import genai
from PIL import Image
import io
from typing import List, Dict, Any, Optional
from app.database.mongodb import get_database
from fastapi import status

router = APIRouter()

# Pydantic model for output schema
class GeminiVisionResponse(BaseModel):
    porduct_name: str   # Optional field for product name
    ingredient: List[str]
    nutrition_values: Dict[str, Any]
    components: Dict[str, str]  # e.g., {"1": "component1", "2": "component2"}
    alternate_home_made_recipe: str

# Ensure your environment has GOOGLE_API_KEY
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Use a current Gemini model (e.g. gemini‑2.5‑flash)
MODEL_NAME = "gemini-2.5-flash"

async def get_gemini_response(image_bytes: bytes) -> GeminiVisionResponse:
    img = Image.open(io.BytesIO(image_bytes))
    contents = [
        "Analyze the food in this image and respond ONLY with a valid JSON object with the following fields: 'porduct_name' (string, the product name), 'ingredient' (list of ingredients), 'nutrition_values' (dictionary of nutrition facts), 'components' (dictionary with numbered components), and 'alternate_home_made_recipe' (string with a homemade recipe alternative). Do not include any text or explanation before or after the JSON. If the product name is not clear, use a best guess or 'Unknown'.",
        img
    ]
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents
    )
    import json
    # Debug: print/log the raw response for troubleshooting
    print('Gemini raw response:', response.text)
    raw = response.text.strip()
    # Remove code block markers if present
    if raw.startswith('```json'):
        raw = raw[len('```json'):].strip()
    if raw.startswith('```'):
        raw = raw[len('```'):].strip()
    if raw.endswith('```'):
        raw = raw[:-3].strip()
    if not raw:
        raise HTTPException(status_code=500, detail="Gemini returned an empty response.")
    try:
        data = json.loads(raw)
        return GeminiVisionResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {e}. Raw response: {raw}")

@router.post("/vision", response_model=GeminiVisionResponse)
async def gemini_vision(
    file: UploadFile = File(...),
    user_id: str = None,  # You may want to use Depends(get_current_user) for real auth
    db=Depends(get_database)
):
    try:
        img_bytes = await file.read()
        result = await get_gemini_response(image_bytes=img_bytes)
        # Store the result in the 'history' collection
        history_doc = {
            "user_id": user_id,
            "response": result.dict(),
            "timestamp": __import__('datetime').datetime.utcnow()
        }
        db['history'].insert_one(history_doc)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
