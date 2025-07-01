from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
from dotenv import load_dotenv
from src.db.database import Database
from src.config.db_config import DATABASE_URL
from .routes import articles, players, analysis
from .routes import vector_search
from .routes import enhanced_search
from .routes import chat
from .routes import admin

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
        # Don't raise exception, just log and continue
        logger.warning("Continuing without database connection")
    
    yield
    
    # Shutdown
    try:
        await Database.close_db()
        logger.info("Closed PostgreSQL connection")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Football News DB API (Debug Mode)",
    description="API for accessing football news and analysis - DEBUG MODE WITHOUT RATE LIMITING",
    version="1.0.0-debug",
    lifespan=lifespan
)

# Configure CORS (NO RATE LIMITING MIDDLEWARE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(articles.router, prefix="/api/v1/articles", tags=["articles"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(vector_search.router, prefix="/api/v1/vector", tags=["vector-search"])
app.include_router(enhanced_search.router,  prefix="/api/v1/search", tags=["enhanced-search"])
app.include_router(chat.router,  prefix="/api/v1/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Football News DB API - DEBUG MODE",
        "version": "1.0.0-debug",
        "status": "operational",
        "warning": "RATE LIMITING DISABLED - DEBUG MODE ONLY"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rate_limiting": "DISABLED",
        "mode": "debug"
    } 