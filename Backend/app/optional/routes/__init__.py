"""
Router initialization file - minimal for demo
"""
from .auth import router as auth_router
from .documents_minimal import router as documents_router
# Temporarily disabled to get server running:
# from .dashboard import router as dashboard_router
# from .settings import router as settings_router
# from .alerts import router as alerts_router
# from .email import router as email_router
# from .cloud import router as cloud_router

__all__ = [
    "auth_router",
    "documents_router", 
    # "dashboard_router",
    # "settings_router",
    # "alerts_router",
    # "email_router",
    # "cloud_router"
]