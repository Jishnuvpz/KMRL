"""
Email processing routes for KMRL Document Management System
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from app.db import get_db
from app.services.email_service import get_email_service
from app.utils.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["Email Processing"])


@router.get("/fetch", response_model=Dict[str, Any])
async def fetch_recent_emails(
    hours: int = Query(default=24, description="Number of hours to look back"),
    max_emails: int = Query(
        default=50, description="Maximum number of emails to fetch"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch recent emails from zodiacmrv@gmail.com
    """
    try:
        email_service = get_email_service(db)
        emails = await email_service.fetch_recent_emails(hours=hours, max_emails=max_emails)

        return {
            "success": True,
            "data": {
                "emails": emails,
                "count": len(emails),
                "hours_back": hours,
                "message": f"Fetched {len(emails)} emails from the last {hours} hours"
            }
        }

    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.post("/process-to-documents", response_model=Dict[str, Any])
async def process_emails_to_documents(
    hours: int = Query(default=24, description="Number of hours to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch emails and convert attachments to documents
    """
    try:
        email_service = get_email_service(db)
        result = await email_service.process_emails_to_documents(hours=hours)

        if result['success']:
            return {
                "success": True,
                "data": {
                    "emails_processed": result['emails_fetched'],
                    "documents_created": result['documents_created'],
                    "documents": result['documents'],
                    "message": f"Created {result['documents_created']} documents from {result['emails_fetched']} emails"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        logger.error(f"Error processing emails to documents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process emails: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def email_service_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check email service configuration and status
    """
    try:
        email_service = get_email_service(db)

        # Test IMAP connection
        mail = await email_service.connect_imap()
        connection_status = "connected" if mail else "failed"

        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass

        return {
            "success": True,
            "data": {
                "email_source": email_service.email_data_source,
                "imap_server": email_service.imap_server,
                "smtp_server": email_service.smtp_server,
                "connection_status": connection_status,
                "configured": bool(email_service.email_username and email_service.email_password)
            }
        }

    except Exception as e:
        logger.error(f"Error checking email status: {e}")
        return {
            "success": False,
            "data": {
                "connection_status": "error",
                "error": str(e),
                "configured": False
            }
        }


@router.get("/test-connection")
async def test_email_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test email connection without fetching emails
    """
    try:
        email_service = get_email_service(db)
        mail = await email_service.connect_imap()

        if mail:
            # Get basic mailbox info
            mail.select('INBOX')
            status, messages = mail.search(None, 'ALL')
            total_emails = len(messages[0].split()) if status == 'OK' else 0

            mail.close()
            mail.logout()

            return {
                "success": True,
                "message": "Email connection successful",
                "data": {
                    "connected": True,
                    "total_emails_in_inbox": total_emails,
                    "email_account": email_service.email_data_source
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to email server",
                "data": {
                    "connected": False,
                    "error": "IMAP connection failed"
                }
            }

    except Exception as e:
        logger.error(f"Email connection test failed: {e}")
        return {
            "success": False,
            "message": "Email connection test failed",
            "data": {
                "connected": False,
                "error": str(e)
            }
        }
