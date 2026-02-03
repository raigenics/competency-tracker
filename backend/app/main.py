"""
FastAPI application for the Competency Tracking System.
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.routes.import_excel import router as import_router
from app.api.routes.employees import router as employees_router
from app.api.routes.skills import router as skills_router
from app.api.routes.competencies import router as competencies_router
from app.api.routes.dropdown import router as dropdown_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.capability_finder import router as capability_finder_router
from app.db.init_db import create_all_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Competency Tracking System API",
    description="Backend API for the Audiology Competency Tracking System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local Vite dev
        "http://localhost:3000",
        "https://thankful-sand-04d55ff00.6.azurestaticapps.net",  # your SWA
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under /api prefix
app.include_router(import_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(skills_router, prefix="/api")
app.include_router(competencies_router, prefix="/api")
app.include_router(dropdown_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(capability_finder_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting up Competency Tracking System API")
    try:
        # NOTE: Table creation can be slow on remote databases
        # Tables are auto-created on first query if they don't exist
        logger.info("Database initialization deferred to first request")
        # create_all_tables()
        # logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Competency Tracking System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "competency-tracking-api"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
