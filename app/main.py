from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, genai, get_history, profile, dashboard

app = FastAPI(
    title="Health GenAI API",
    description="A FastAPI backend for health-related AI services",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/v1/user", tags=["User Profile"])
app.include_router(genai.router, prefix="/api/v1/genai", tags=["GenAI"])
app.include_router(get_history.router, prefix="/api/v1/genai", tags=["GenAI History"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Health GenAI API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)