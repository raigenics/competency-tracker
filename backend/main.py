"""
Entry point for running the FastAPI application directly from backend root.
This allows running: uvicorn main:app --reload
"""
from app.main import app

# Re-export the app instance
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
