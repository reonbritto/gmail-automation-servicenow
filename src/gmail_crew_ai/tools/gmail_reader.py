import imaplib
import email
import os
from typing import List, Dict, Any, Optional
from email.header import decode_header
from datetime import datetime
import re
from pydantic import BaseModel, Field

class EmailData(BaseModel):
    """Structure for email data"""
    subject: str = Field(description="Email subject")
    sender: str = Field(description="Email sender")
    date: str = Field(description="Email date")
    body: str = Field(description="Email body content")
    message_id: str = Field(description="Unique message ID")
    is_servicenow: bool = Field(default=False, description="Whether email is from ServiceNow")
    priority: str = Field(default="normal", description="Email priority (high, normal, low)")

def read_gmail_emails(limit: int = 5) -> Dict[str, Any]:
    """
    Read unread emails from Gmail inbox using IMAP connection
    
    Args:
        limit: Maximum number of emails to fetch (default: 5)
        
    Returns:
        Dictionary with emails list or error message
    """
    email_address = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("APP_PASSWORD")
    
    if not email_address or not app_password:
        return {"error": "EMAIL_ADDRESS and APP_PASSWORD must be set in environment variables"}
    
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, app_password)
        
        # Select inbox
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            return {"error": "Failed to search for emails"}
        
        email_ids = messages[0].split()
        
        if not email_ids:
            return {"message": "No unread emails found", "emails": []}
        
        # Limit the number of emails to process
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        
        emails = []
        
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                # Parse email
                email_message = email.message_from_bytes(msg_data[0][1])
                
                # Extract email data
                email_data = _extract_email_data(email_message)
                
                if email_data:
                    emails.append(email_data)
                    
            except Exception as e:
                print(f"Error processing email {email_id}: {str(e)}")
                continue
        
        # Close connection
        mail.close()
        mail.logout()
        
        return {"emails": emails, "count": len(emails)}
        
    except Exception as e:
        return {"error": f"Failed to connect to Gmail: {str(e)}"}

def _extract_email_data(email_message: email.message.Message) -> Optional[Dict[str, Any]]:
    """Extract relevant data from email message"""
    try:
        # Extract subject
        subject = _decode_header(email_message.get("Subject", ""))
        
        # Extract sender
        sender = _decode_header(email_message.get("From", ""))
        
        # Extract date
        date = email_message.get("Date", "")
        
        # Extract message ID
        message_id = email_message.get("Message-ID", "")
        
        # Extract body
        body = _extract_body(email_message)
        
        # Determine if it's ServiceNow email
        is_servicenow = _is_servicenow_email(sender, subject, body)
        
        # Determine priority
        priority = _determine_priority(sender, subject, body, is_servicenow)
        
        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,
            "message_id": message_id,
            "is_servicenow": is_servicenow,
            "priority": priority
        }
        
    except Exception as e:
        print(f"Error extracting email data: {str(e)}")
        return None

def _decode_header(header: str) -> str:
    """Decode email header"""
    if not header:
        return ""
    
    try:
        decoded = decode_header(header)
        header_parts = []
        
        for part, encoding in decoded:
            if isinstance(part, bytes):
                if encoding:
                    part = part.decode(encoding)
                else:
                    part = part.decode('utf-8', errors='ignore')
            header_parts.append(part)
        
        return ''.join(header_parts)
    except Exception:
        return str(header)

def _extract_body(email_message: email.message.Message) -> str:
    """Extract email body content"""
    body = ""
    
    try:
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        html_content = payload.decode(charset, errors='ignore')
                        # Simple HTML to text conversion
                        body += _html_to_text(html_content)
        else:
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
            elif content_type == "text/html":
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    html_content = payload.decode(charset, errors='ignore')
                    body = _html_to_text(html_content)
    
    except Exception as e:
        print(f"Error extracting body: {str(e)}")
        body = "Error extracting email content"
    
    return body.strip()

def _html_to_text(html_content: str) -> str:
    """Simple HTML to text conversion"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except ImportError:
        # Fallback: simple regex-based HTML stripping
        import re
        text = re.sub('<[^<]+?>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

def _is_servicenow_email(sender: str, subject: str, body: str) -> bool:
    """Determine if email is from ServiceNow"""
    servicenow_indicators = [
        "servicenow",
        "service-now",
        "do-not-reply",
        "incident",
        "request",
        "ticket",
        "INC",
        "REQ",
        "CHG",
        "RITM"
    ]
    
    text_to_check = f"{sender} {subject} {body}".lower()
    
    return any(indicator in text_to_check for indicator in servicenow_indicators)

def _determine_priority(sender: str, subject: str, body: str, is_servicenow: bool) -> str:
    """Determine email priority"""
    high_priority_indicators = [
        "urgent",
        "high priority",
        "critical",
        "emergency",
        "asap",
        "immediate",
        "p1",
        "severity 1"
    ]
    
    low_priority_indicators = [
        "newsletter",
        "no-reply",
        "noreply",
        "automated",
        "marketing",
        "promotion",
        "unsubscribe"
    ]
    
    text_to_check = f"{sender} {subject} {body}".lower()
    
    if any(indicator in text_to_check for indicator in high_priority_indicators):
        return "high"
    elif any(indicator in text_to_check for indicator in low_priority_indicators):
        return "low"
    elif is_servicenow:
        return "high"
    else:
        return "normal"
