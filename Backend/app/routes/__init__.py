"""
Router initialization - Complete KMRL System
"""
from . import auth
from . import documents
from . import email_routes
from . import summarization_routes

__all__ = [
    "auth",
    "documents",
    "email_routes",
    "summarization_routes"
]
