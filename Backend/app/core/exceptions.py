"""
Exception handling utilities for KMRL Document Management System
"""
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class DocumentManagementException(Exception):
    """Base exception for Document Management System"""

    def __init__(self, message: str, code: str = "GENERAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class OCRException(DocumentManagementException):
    """Exception for OCR-related errors"""

    def __init__(self, message: str, code: str = "OCR_ERROR"):
        super().__init__(message, code, 422)


class SummarizationException(DocumentManagementException):
    """Exception for summarization-related errors"""

    def __init__(self, message: str, code: str = "SUMMARIZATION_ERROR"):
        super().__init__(message, code, 422)


class StorageException(DocumentManagementException):
    """Exception for storage-related errors"""

    def __init__(self, message: str, code: str = "STORAGE_ERROR"):
        super().__init__(message, code, 503)


class AuthenticationException(DocumentManagementException):
    """Exception for authentication-related errors"""

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code, 401)


def create_success_response(
    data: Any = None,
    message: str = "Success",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized success response"""

    response = {
        "success": True,
        "message": message
    }

    if data is not None:
        response["data"] = data

    if metadata:
        response["metadata"] = metadata

    return response


def create_error_response(
    message: str,
    code: str = "ERROR",
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create a standardized error response"""

    content = {
        "success": False,
        "error": {
            "message": message,
            "code": code,
            "type": "CustomError"
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers for the application"""

    @app.exception_handler(DocumentManagementException)
    async def document_management_exception_handler(request: Request, exc: DocumentManagementException):
        """Handle custom Document Management exceptions"""
        logger.error(
            f"DocumentManagementException: {exc.message} (Code: {exc.code})")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.message,
                    "code": exc.code,
                    "type": exc.__class__.__name__
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        logger.warning(
            f"HTTPException: {exc.detail} (Status: {exc.status_code})")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.detail,
                    "code": f"HTTP_{exc.status_code}",
                    "type": "HTTPException"
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "message": "Request validation failed",
                    "code": "VALIDATION_ERROR",
                    "type": "RequestValidationError",
                    "details": exc.errors()
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.error(
            f"Starlette HTTPException: {exc.detail} (Status: {exc.status_code})")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": str(exc.detail),
                    "code": f"HTTP_{exc.status_code}",
                    "type": "StarletteHTTPException"
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "message": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "type": "Exception"
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )
