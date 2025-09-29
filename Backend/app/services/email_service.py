"""
Email Service for KMRL Document Management System
Fetches emails from zodiacmrv@gmail.com and processes attachments
"""
import os
import logging
import email
import imaplib
import smtplib
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, db: Session = None):
        self.db = db
        self.imap_server = "imap.gmail.com"
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.email_address = settings.EMAIL_DATA_SOURCE
        self.password = settings.SMTP_PASSWORD

    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            return mail
        except Exception as e:
            raise Exception(f"Failed to connect to email server: {str(e)}")

    def fetch_recent_emails(self, hours: int = 24, store_raw: bool = True, user_id: str = None) -> List[Dict]:
        """Fetch recent emails from the configured email address"""
        try:
            mail = self.connect_imap()
            mail.select(settings.EMAIL_FOLDER)

            # Calculate date for search
            since_date = (datetime.now() - timedelta(hours=hours)
                          ).strftime("%d-%b-%Y")

            # Search for recent emails
            status, messages = mail.search(None, f'SINCE {since_date}')

            if status != 'OK':
                raise Exception("Failed to search emails")

            email_ids = messages[0].split()
            emails = []

            # Limit the number of emails to fetch
            max_emails = min(len(email_ids), settings.EMAIL_MAX_FETCH)

            for i in range(max_emails):
                email_id = email_ids[-(i+1)]  # Get most recent first

                status, msg_data = mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                email_message = email.message_from_bytes(msg_data[0][1])

                # Extract email data
                email_data = {
                    'id': email_id.decode(),
                    'subject': email_message.get('Subject', ''),
                    'from': email_message.get('From', ''),
                    'to': email_message.get('To', ''),
                    'date': email_message.get('Date', ''),
                    'body': self._extract_email_body(email_message),
                    'attachments': self._extract_attachments(email_message),
                    'timestamp': datetime.now().isoformat(),
                    'headers': dict(email_message.items()),
                    'raw_message_id': email_message.get('Message-ID', ''),
                    'content_type': email_message.get_content_type(),
                    'size': len(msg_data[0][1]) if msg_data and msg_data[0] else 0
                }

                emails.append(email_data)

            mail.close()
            mail.logout()

            return emails

        except Exception as e:
            raise Exception(f"Failed to fetch emails: {str(e)}")

    def _extract_email_body(self, email_message) -> str:
        """Extract email body content"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body += part.get_payload(decode=True).decode('utf-8',
                                                                 errors='ignore')
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    # For HTML emails, you might want to convert to plain text
                    html_body = part.get_payload(
                        decode=True).decode('utf-8', errors='ignore')
                    # Simple HTML tag removal (consider using BeautifulSoup for better parsing)
                    body += re.sub('<[^<]+?>', '', html_body)
        else:
            body = email_message.get_payload(
                decode=True).decode('utf-8', errors='ignore')

        return body.strip()

    def _extract_attachments(self, email_message) -> List[Dict]:
        """Extract email attachments information"""
        attachments = []

        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })

        return attachments

    def process_emails_for_documents(self, emails: List[Dict], user_id: int) -> List[Dict]:
        """Process emails to extract potential documents and important information"""
        processed_results = []

        for email_data in emails:
            # Check if email contains document-related keywords
            document_keywords = [
                'invoice', 'receipt', 'statement', 'report', 'contract',
                'agreement', 'document', 'attachment', 'pdf', 'file'
            ]

            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()

            is_document_related = any(
                keyword in subject or keyword in body for keyword in document_keywords)

            result = {
                'email_id': email_data['id'],
                'subject': email_data['subject'],
                'from': email_data['from'],
                'date': email_data['date'],
                'is_document_related': is_document_related,
                'attachments_count': len(email_data.get('attachments', [])),
                'key_information': self._extract_key_information(email_data),
                'processed_at': datetime.now().isoformat()
            }

            processed_results.append(result)

        return processed_results

    def _extract_key_information(self, email_data: Dict) -> Dict:
        """Extract key information from email using pattern matching"""
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')

        key_info = {
            'amounts': [],
            'dates': [],
            'organizations': [],
            'phone_numbers': [],
            'email_addresses': []
        }

        # Extract monetary amounts
        amount_pattern = r'[\$€£¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY)'
        key_info['amounts'] = re.findall(amount_pattern, body, re.IGNORECASE)

        # Extract dates
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        key_info['dates'] = re.findall(date_pattern, body)

        # Extract phone numbers
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        key_info['phone_numbers'] = re.findall(phone_pattern, body)

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        key_info['email_addresses'] = re.findall(email_pattern, body)

        # Extract potential organization names (basic pattern)
        org_pattern = r'\b[A-Z][a-z]+\s+(?:Inc|LLC|Corp|Ltd|Company|Co\.|Corporation)\b'
        key_info['organizations'] = re.findall(org_pattern, body)

        return key_info

    def send_notification_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send notification email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.password)

            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()

            return True

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def get_email_statistics(self, hours: int = 24) -> Dict:
        """Get email statistics for the specified time period"""
        try:
            emails = self.fetch_recent_emails(hours)

            total_emails = len(emails)
            document_related = sum(1 for email in emails
                                   if any(keyword in email.get('subject', '').lower() or
                                          keyword in email.get(
                                       'body', '').lower()
                                       for keyword in ['invoice', 'receipt', 'document', 'report']))

            with_attachments = sum(1 for email in emails
                                   if email.get('attachments'))

            return {
                'total_emails': total_emails,
                'document_related': document_related,
                'with_attachments': with_attachments,
                'time_period_hours': hours,
                'fetch_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'total_emails': 0,
                'document_related': 0,
                'with_attachments': 0
            }


# Singleton instance
_email_service = None


def get_email_service(db: Session = None) -> EmailService:
    """Get email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService(db)
    elif db and not _email_service.db:
        _email_service.db = db
    return _email_service
