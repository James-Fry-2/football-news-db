from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Football News DB API",
    description="API for accessing football news and analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "football_news")

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
        app.mongodb = app.mongodb_client[DB_NAME]
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    logger.info("Closed MongoDB connection")

# Import routes
from .routes import articles, players, analysis

# Register routes
app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Football News DB API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    try:
        # Check database connection
        await app.mongodb.command("ping")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable") 