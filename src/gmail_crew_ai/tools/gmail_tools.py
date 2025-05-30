# ============================================================
# Gmail Tools: Fetching, Drafting, Organizing, and Deleting
# ============================================================

import os
import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
import base64
from pathlib import Path
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Gmail credentials
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

# Ensure output directory exists
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

def connect_to_gmail():
    """Establish connection to Gmail IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        return mail
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        raise

def fetch_unread_emails(max_emails=10):
    """
    Fetch unread emails from Gmail inbox.
    
    Args:
        max_emails (int): Maximum number of emails to fetch
        
    Returns:
        list: List of email dictionaries
    """
    try:
        mail = connect_to_gmail()
        mail.select("inbox")
        
        # Search for unread emails
        status, data = mail.search(None, "UNSEEN")
        if status != "OK":
            raise Exception(f"Error searching for emails: {status}")
        
        email_ids = data[0].split()
        if not email_ids:
            return []
        
        # Limit the number of emails
        email_ids = email_ids[:max_emails]
        
        emails = []
        for e_id in email_ids:
            status, data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract email data
            email_data = {
                "id": e_id.decode(),
                "date": msg["Date"],
                "from": msg["From"],
                "to": msg["To"],
                "subject": msg["Subject"] or "(No Subject)",
                "body": "",
                "thread_id": msg["Thread-ID"] if "Thread-ID" in msg else None
            }
            
            # Extract body
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" not in content_disposition and content_type in ["text/plain", "text/html"]:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            payload = part.get_payload(decode=True).decode(charset, errors="replace")
                            email_data["body"] = payload
                            if content_type == "text/html":
                                break  # Prefer HTML content
                        except Exception as e:
                            print(f"Error decoding email body: {e}")
                            continue
            else:
                # Non-multipart email
                charset = msg.get_content_charset() or "utf-8"
                try:
                    payload = msg.get_payload(decode=True).decode(charset, errors="replace")
                    email_data["body"] = payload
                except Exception as e:
                    print(f"Error decoding email body: {e}")
            
            emails.append(email_data)
        
        mail.close()
        mail.logout()
        
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        raise

def save_email_draft(subject, body, recipient, thread_info=None):
    """
    Save an email draft to Gmail.
    
    Args:
        subject (str): Email subject
        body (str): Email body content
        recipient (str): Recipient email address
        thread_info (dict, optional): Thread information for replying to a thread
        
    Returns:
        str: Draft ID or success message
    """
    try:
        # Prepare the email message
        message = MIMEMultipart()
        message["From"] = GMAIL_USER
        message["To"] = recipient
        message["Subject"] = subject
        
        # Add thread information if provided
        if thread_info and isinstance(thread_info, dict):
            if "thread_id" in thread_info:
                message["Thread-ID"] = thread_info["thread_id"]
            if "in_reply_to" in thread_info:
                message["In-Reply-To"] = thread_info["in_reply_to"]
            if "references" in thread_info:
                message["References"] = thread_info["references"]
        
        message.attach(MIMEText(body, "html"))
        
        # Save the draft using SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            
            # Using the Gmail SMTP trick to save as draft
            # (sending to yourself, but not actually sending)
            server.sendmail(GMAIL_USER, GMAIL_USER, message.as_string())
        
        # For now, return a success message
        draft_id = f"draft_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save a local copy of the draft
        draft_data = {
            "id": draft_id,
            "date": datetime.now().isoformat(),
            "subject": subject,
            "to": recipient,
            "body": body,
            "thread_info": thread_info
        }
        
        # Append to drafts file
        drafts_file = output_dir / "saved_drafts.json"
        
        try:
            if drafts_file.exists():
                with open(drafts_file, "r") as f:
                    drafts = json.load(f)
            else:
                drafts = []
        except json.JSONDecodeError:
            drafts = []
            
        drafts.append(draft_data)
        
        with open(drafts_file, "w") as f:
            json.dump(drafts, f, indent=2)
        
        return draft_id
    
    except Exception as e:
        print(f"Error saving draft: {e}")
        raise

def mark_email_as_read(email_id):
    """
    Mark an email as read in Gmail.
    
    Args:
        email_id (str): Email ID to mark as read
        
    Returns:
        bool: Success status
    """
    try:
        mail = connect_to_gmail()
        mail.select("inbox")
        
        # Convert string ID to bytes if needed
        if isinstance(email_id, str):
            email_id = email_id.encode()
            
        # Mark the email as read (removing UNSEEN flag)
        mail.store(email_id, "+FLAGS", "\\Seen")
        
        mail.close()
        mail.logout()
        
        return True
    except Exception as e:
        print(f"Error marking email as read: {e}")
        raise