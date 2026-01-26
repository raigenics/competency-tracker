"""
API routes package for the Competency Tracking System.
Contains individual route modules.
"""

from app.api.routes.import_excel import router as import_router
from app.api.routes.employees import router as employees_router
from app.api.routes.skills import router as skills_router
from app.api.routes.competencies import router as competencies_router
from app.api.routes.dropdown import router as dropdown_router
from app.api.routes.dashboard import router as dashboard_router

__all__ = [
    "import_router", 
    "employees_router", 
    "skills_router", 
    "competencies_router",
    "dropdown_router",
    "dashboard_router"
]
