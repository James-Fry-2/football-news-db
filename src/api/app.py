from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
from dotenv import load_dotenv
from src.db.database import Database
from src.config.db_config import DATABASE_URL
from .routes import articles, players, analysis
from .routes import vector_search
from .routes import enhanced_search

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await Database.connect_db(DATABASE_URL)
        logger.info("Successfully connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    yield
    
    # Shutdown
    try:
        await Database.close_db()
        logger.info("Closed PostgreSQL connection")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Football News DB API",
    description="API for accessing football news and analysis",
    version="1.0.0",
    lifespan=lifespan
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
# MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
# DB_NAME = os.getenv("DB_NAME", "football_news")

# Import routes
# from .routes import articles, players, analysis

# Register routes
app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(vector_search.router, prefix="/api/v1/vector", tags=["vector-search"])
app.include_router(enhanced_search.router,  prefix="/api/v1/search", tags=["enhanced-search"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Football News DB API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    } 