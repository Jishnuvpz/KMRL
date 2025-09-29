"""
CORS configuration for frontend integration
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def setup_cors(app: FastAPI):
    """Setup CORS middleware for frontend integration"""
    
    # Development and production origins
    origins = [
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Alternative dev port
        "http://127.0.0.1:8080",
        # Add production frontend URLs here
        # "https://your-frontend-domain.com",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key"
        ],
        expose_headers=["Content-Range", "X-Content-Range"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    return app
