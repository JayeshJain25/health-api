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

# Updated Pydantic models for detailed output schema
class NutritionFact(BaseModel):
    name: str
    amount: str
    percentage_dv: Optional[str] = None
    category: str  # "good_for_you", "others", "concerns"

class IngredientCategory(BaseModel):
    category_name: str
    count: int
    ingredients: List[str]
    color_code: str  # "green", "yellow", "red", "gray"

class GeminiVisionResponse(BaseModel):
    product_name: str
    serving_size: str
    calories: str
    total_ingredients: int
    ingredient_categories: List[IngredientCategory]
    nutrition_facts: List[NutritionFact]
    concerns: int
    concerns_message: str
    additives: List[str]
    allergens: List[str]
    allergens_message: str
    alternate_home_made_recipe: str
    rating: str  # "poor", "average", "good", "excellent"
    category: str  # "beverage", "cereal", "snack", "meal", etc.
    processing_level: str  # "semi_processed", "processed", "highly_processed"

# Ensure your environment has GOOGLE_API_KEY
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Use a current Gemini model (e.g. gemini‑2.5‑flash)
MODEL_NAME = "gemini-2.5-flash"

async def get_gemini_response(image_bytes: bytes) -> GeminiVisionResponse:
    img = Image.open(io.BytesIO(image_bytes))
    contents = [
        """Analyze the food product in this image and respond ONLY with a valid JSON object with the following detailed structure:

{
  "product_name": "string - the product name",
  "serving_size": "string - serving size (e.g., '30g', '1 cup')",
  "calories": "string - calories per serving (e.g., '154.5')",
  "total_ingredients": "number - total count of ingredients",
  "ingredient_categories": [
    {
      "category_name": "string - category name (e.g., 'Good for You', 'Sugar & Substitutes', 'Refined Grains & Oils', 'Additives', 'Others')",
      "count": "number - count of ingredients in this category",
      "ingredients": ["array of ingredient names"],
      "color_code": "string - 'green' for healthy, 'yellow' for moderate, 'red' for concerning, 'gray' for neutral"
    }
  ],
  "nutrition_facts": [
    {
      "name": "string - nutrient name (e.g., 'Sodium', 'Total Fat')",
      "amount": "string - amount with unit (e.g., '63.69mg', '10.65g')",
      "percentage_dv": "string - percentage daily value (e.g., '2.65%') or null if not applicable",
      "category": "string - 'good_for_you' for beneficial nutrients, 'others' for neutral, 'concerns' for high amounts"
    }
  ],
  "concerns": "number - count of concerning ingredients/aspects",
  "concerns_message": "string - message about concerns (e.g., 'Yay! This Product has NO Ingredient Concerns.' or specific concerns)",
  "additives": ["array of additive ingredients"],
  "allergens": ["array of allergens present"],
  "allergens_message": "string - allergen information message",
  "alternate_home_made_recipe": "string - homemade recipe alternative",
  "rating": "string - 'poor', 'average', 'good', or 'excellent' based on nutritional value",
  "category": "string - food category like 'beverage', 'cereal', 'snack', 'meal', 'dairy', 'bakery', 'candy', 'frozen'",
  "processing_level": "string - 'semi_processed', 'processed', or 'highly_processed'"
}

Guidelines:
- Categorize ingredients as: 'Good for You' (nuts, seeds, whole grains, natural ingredients), 'Sugar & Substitutes' (all sweeteners), 'Refined Grains & Oils' (processed grains/oils), 'Additives' (artificial ingredients, preservatives), 'Others' (neutral ingredients)
- For nutrition_facts, include major nutrients like sodium, carbs, sugars, fiber, protein, fats, vitamins, minerals
- Use green color_code for healthy categories, yellow for moderate, red for concerning, gray for neutral
- Provide detailed percentage daily values based on 2000 calorie diet
- Be specific about serving sizes and calorie counts
- If information is not clearly visible, make reasonable estimates based on similar products

Do not include any text or explanation before or after the JSON.""",
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
