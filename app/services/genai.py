from fastapi import UploadFile
from google_genai import GenAI  # Assuming this is the correct import for the Google GenAI package

genai_client = GenAI()  # Initialize the GenAI client

async def process_image(file: UploadFile):
    contents = await file.read()
    response = genai_client.generate_response(contents)  # Replace with actual method to process the image
    return response