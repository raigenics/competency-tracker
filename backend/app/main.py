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
from app.api.routes.admin_master_import import router as admin_master_import_router
from app.api.routes.rbac_admin import router as rbac_admin_router

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
app.include_router(admin_master_import_router, prefix="/api")
app.include_router(rbac_admin_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting up Competency Tracking System API")
    try:
        # NOTE: Database schema is managed via Alembic migrations
        # Run 'alembic upgrade head' to apply migrations before starting the app
        logger.info("Database migrations should be applied via 'alembic upgrade head'")
        logger.info("Application ready")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
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
