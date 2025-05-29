# ============================================================
# Gmail Tools: Fetching, Drafting, Organizing, and Deleting
# ============================================================

import imaplib
import email
from email.header import decode_header
from typing import List, Tuple, Literal, Optional, Type, Dict, Any
import re
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
import os
from pydantic import BaseModel, Field
from crewai.tools import tool
import time
import datetime  # Add this import
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
import json

# -------------------------------
# Utility Functions
# -------------------------------

def decode_header_safe(header):
    """
    Safely decode email headers that might contain encoded words or non-ASCII characters.
    """
    try:
        decoded_parts = []
        for decoded_str, charset in decode_header(header):
            if isinstance(decoded_str, bytes):
                if charset:
                    decoded_parts.append(decoded_str.decode(charset or 'utf-8', errors='replace'))
                else:
                    decoded_parts.append(decoded_str.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(decoded_str))
        return ' '.join(decoded_parts)
    except Exception as e:
        # Fallback to raw header if decoding fails
        return str(header)

def clean_email_body(email_body: str) -> str:
    """
    Clean the email body by removing HTML tags and excessive whitespace.
    """
    try:
        soup = BeautifulSoup(email_body, "html.parser")
        text = soup.get_text(separator=" ")  # Get text with spaces instead of <br/>
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        text = email_body  # Fallback to raw body if parsing fails
    # Remove excessive whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_thread_history(thread_history: Dict[str, Any]) -> str:
    """
    Format thread history into a readable string.
    """
    if not thread_history or "error" in thread_history:
        return f"Error retrieving thread history: {thread_history.get('error', 'Unknown error')}"
    
    messages = thread_history.get("thread_messages", [])
    if not messages:
        return "No messages found in thread history."
    
    formatted = f"Thread: {thread_history.get('thread_subject', 'No Subject')}\n"
    formatted += f"Participants: {', '.join(thread_history.get('participants', []))}\n"
    formatted += f"Total Messages: {thread_history.get('message_count', 0)}\n\n"
    
    # Add each message in chronological order
    for i, msg in enumerate(messages, 1):
        formatted += f"--- Message {i} ---\n"
        formatted += f"From: {msg.get('sender', 'Unknown')}\n"
        formatted += f"To: {msg.get('to', 'Unknown')}\n"
        formatted += f"Date: {msg.get('date', 'Unknown')}\n"
        formatted += f"Subject: {msg.get('subject', 'No Subject')}\n"
        
        # Add attachment info if available
        if 'attachments' in msg and msg['attachments']:
            formatted += "Attachments:\n"
            for att in msg['attachments']:
                formatted += f"  - {att.get('filename', 'Unknown')} ({att.get('type', 'Unknown')}, {att.get('size', 0)} bytes)\n"
        formatted += f"\n{msg.get('body', 'No content')}\n\n"
    
    return formatted

# -------------------------------
# Base Gmail Tool
# -------------------------------

class GmailToolBase(BaseTool):
    """Base class for Gmail tools, handling connection and credentials."""
    class Config:
        arbitrary_types_allowed = True

    email_address: Optional[str] = Field(None, description="Gmail email address")
    app_password: Optional[str] = Field(None, description="Gmail app password")

    def __init__(self, description: str = ""):
        super().__init__(description=description)
        self.email_address = os.environ.get("EMAIL_ADDRESS")
        self.app_password = os.environ.get("APP_PASSWORD")
        if not self.email_address or not self.app_password:
            raise ValueError("EMAIL_ADDRESS and APP_PASSWORD must be set in the environment.")

    def _connect(self):
        """Connect to Gmail."""
        try:
            print(f"Connecting to Gmail with email: {self.email_address[:3]}...{self.email_address[-8:]}")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.app_password)
            print("Successfully logged in to Gmail")
            return mail
        except Exception as e:
            print(f"Error connecting to Gmail: {e}")
            raise e

    def _disconnect(self, mail):
        """Disconnect from Gmail."""
        try:
            mail.close()
            mail.logout()
            print("Successfully disconnected from Gmail")
        except:
            pass

    def _get_thread_messages(self, mail: imaplib.IMAP4_SSL, msg) -> List[Dict[str, Any]]:
        """Get all messages in the thread by following References and In-Reply-To headers."""
        thread_messages = []

        # Get message IDs from References and In-Reply-To headers
        references = msg.get("References", "").split()
        in_reply_to = msg.get("In-Reply-To", "").split()
        current_msg_id = msg.get("Message-ID", "").strip()
        
        # Combine all message IDs, including the current one
        message_ids = list(set(references + in_reply_to + [current_msg_id]))
        message_ids = [mid for mid in message_ids if mid]  # Remove empty strings
        
        if message_ids:
            # Build a complex search query that looks for these message IDs in any relevant header
            search_terms = []
            for mid in message_ids:
                search_terms.append(f'HEADER Message-ID "{mid}"')
                search_terms.append(f'HEADER References "{mid}"')
                search_terms.append(f'HEADER In-Reply-To "{mid}"')
            search_query = ' OR '.join(search_terms)

            try:
                result, data = mail.search(None, search_query)
                if result == "OK" and data[0]:
                    thread_ids = data[0].split()
                    print(f"Found {len(thread_ids)} messages in thread")
                    
                    for thread_id in thread_ids:
                        result, msg_data = mail.fetch(thread_id, "(RFC822)")
                        if result == "OK":
                            thread_msg = email.message_from_bytes(msg_data[0][1])
                            
                            # Extract useful metadata and body
                            message_info = {
                                "subject": decode_header_safe(thread_msg["Subject"]),
                                "sender": decode_header_safe(thread_msg["From"]),
                                "date": thread_msg["Date"],
                                "body": self._extract_body(thread_msg),
                                "message_id": thread_msg.get("Message-ID", ""),
                                "email_id": thread_id.decode('utf-8')
                            }
                            
                            thread_messages.append(message_info)
            except Exception as e:
                print(f"Error searching for thread messages: {e}")
        
        # Sort messages by date
        thread_messages.sort(key=lambda x: email.utils.parsedate_to_datetime(x['date']) 
                          if x.get('date') and email.utils.parsedate_to_datetime(x['date']) 
                          else datetime.datetime.min)
        return thread_messages

    def _extract_body(self, msg) -> str:
        """Extract body from an email message."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                try:
                    email_body = part.get_payload(decode=True).decode()
                except:
                    email_body = ""

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body += email_body
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    body += clean_email_body(email_body)
        else:
            try:
                body = clean_email_body(msg.get_payload(decode=True).decode())
            except Exception as e:
                body = f"Error decoding body: {e}"
        return body

# -------------------------------
# Get Unread Emails Tool
# -------------------------------

class GetUnreadEmailsSchema(BaseModel):
    """Schema for GetUnreadEmailsTool input."""
    limit: Optional[int] = Field(
        default=5,
        description="Maximum number of unread emails to retrieve. Defaults to 5.",
        ge=1  # Ensures the limit is greater than or equal to 1
    )

class GetUnreadEmailsTool(GmailToolBase):
    """Tool to get unread emails from Gmail."""
    name: str = "get_unread_emails"
    description: str = "Gets unread emails from Gmail"
    args_schema: Type[BaseModel] = GetUnreadEmailsSchema

    def _run(self, limit: Optional[int] = 5) -> List[Tuple[str, str, str, str, Dict]]:
        """
        Fetch unread emails from Gmail up to the specified limit.
        Returns a list of tuples: (subject, sender, body, email_id, thread_info)
        """
        mail = self._connect()
        try:
            print("DEBUG: Connecting to Gmail...")
            mail.select("INBOX")
            result, data = mail.search(None, 'UNSEEN')
            
            print(f"DEBUG: Search result: {result}")
            
            if result != "OK":
                print("DEBUG: Error searching for unseen emails")
                return []
            email_ids = data[0].split()
            print(f"DEBUG: Found {len(email_ids)} unread emails")
            if not email_ids:
                print("DEBUG: No unread emails found.")
                return []
            
            email_ids = list(reversed(email_ids))
            email_ids = email_ids[:limit]
            print(f"DEBUG: Processing {len(email_ids)} emails")
            emails = []
            for i, email_id in enumerate(email_ids):
                print(f"DEBUG: Processing email {i+1}/{len(email_ids)}")
                result, msg_data = mail.fetch(email_id, "(RFC822)")
                if result != "OK":
                    print(f"Error fetching email {email_id}:", result)
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decode headers properly (handles encoded characters)
                subject = decode_header_safe(msg["Subject"])
                sender = decode_header_safe(msg["From"])
                
                # Extract and standardize the date
                date_str = msg.get("Date", "")
                received_date = self._parse_email_date(date_str)
                
                # Get the current message body
                current_body = self._extract_body(msg)
                
                # Get thread messages
                thread_messages = self._get_thread_messages(mail, msg)
                
                # Combine current message with thread history
                full_body = "\n\n--- Previous Messages ---\n".join([current_body] + thread_messages)
                
                # Get thread metadata
                thread_info = {
                    'message_id': msg.get('Message-ID', ''),
                    'in_reply_to': msg.get('In-Reply-To', ''),
                    'references': msg.get('References', ''),
                    'date': received_date,  # Use standardized date
                    'raw_date': date_str,   # Keep original date string
                    'email_id': email_id.decode('utf-8')
                }
                
                # Add a clear date indicator in the body for easier extraction
                full_body = f"EMAIL DATE: {received_date}\n\n{full_body}"
                
                # Print the structure of what we're appending
                print(f"DEBUG: Email tuple structure: subject={subject}, sender={sender}, body_length={len(full_body)}, email_id={email_id.decode('utf-8')}, thread_info_keys={thread_info.keys()}")
                emails.append((subject, sender, full_body, email_id.decode('utf-8'), thread_info))
            
            print(f"DEBUG: Returning {len(emails)} email tuples")
            return emails
        except Exception as e:
            print(f"DEBUG: Exception in GetUnreadEmailsTool: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self._disconnect(mail)

    def _parse_email_date(self, date_str: str) -> str:
        """
        Parse email date string into a standardized format (YYYY-MM-DD).
        """
        if not date_str:
            return ""
        
        try:
            # Try various date formats commonly found in emails
            # Remove timezone name if present (like 'EDT', 'PST')
            date_str = re.sub(r'\s+\([A-Z]{3,4}\)', '', date_str)
            # Parse with email.utils
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
        
        return ""

# -------------------------------
# Save Draft Tool
# -------------------------------

class SaveDraftSchema(BaseModel):
    """Schema for SaveDraftTool input."""
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    recipient: str = Field(..., description="Recipient email address")
    thread_info: Optional[Dict[str, Any]] = Field(None, description="Thread information for replies")

class SaveDraftTool(BaseTool):
    """Tool to save an email as a draft using IMAP."""
    name: str = "save_email_draft"
    description: str = "Saves an email as a draft in Gmail"
    args_schema: Type[BaseModel] = SaveDraftSchema

    def _format_body(self, body: str) -> str:
        """Format the email body with signature."""
        # Replace [Your name] or [Your Name] with Reon
        body = re.sub(r'\[Your [Nn]ame\]', 'Reon', body)
        
        # If no placeholder was found, append the signature
        if '[Your' not in body and '[your' not in body:
            # Create a professional signature
            signature = "\n"
            body = f"{body}{signature}"
        
        return body

    def _connect(self):
        """Connect to Gmail using IMAP."""
        # Get email credentials from environment
        email_address = os.environ.get('EMAIL_ADDRESS')
        app_password = os.environ.get('APP_PASSWORD')
        
        if not email_address or not app_password:
            raise ValueError("EMAIL_ADDRESS or APP_PASSWORD environment variables not set")
        
        # Connect to Gmail's IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        print(f"Connecting to Gmail with email: {email_address[:3]}...{email_address[-10:]}")
        mail.login(email_address, app_password)
        return mail, email_address

    def _disconnect(self, mail):
        """Disconnect from Gmail."""
        try:
            mail.logout()
        except:
            pass

    def _check_drafts_folder(self, mail):
        """Check available mailboxes to find the drafts folder."""
        print("Checking available mailboxes...")
        result, mailboxes = mail.list()
        if result == 'OK':
            drafts_folders = []
            for mailbox in mailboxes:
                if b'Drafts' in mailbox or b'Draft' in mailbox:
                    drafts_folders.append(mailbox.decode())
                    print(f"Found drafts folder: {mailbox.decode()}")
            return drafts_folders
        return []

    def _verify_draft_saved(self, mail, subject, recipient):
        """Verify if the draft was actually saved by searching for it."""
        try:
            # Try different drafts folder names
            drafts_folders = [
                '"[Gmail]/Drafts"', 
                'Drafts',
                'DRAFTS',
                '"[Google Mail]/Drafts"',
                '[Gmail]/Drafts'
            ]
            for folder in drafts_folders:
                try:
                    print(f"Checking folder: {folder}")
                    result, _ = mail.select(folder, readonly=True)
                    if result != 'OK':
                        continue
                        
                    # Search for drafts with this subject
                    search_criteria = f'SUBJECT "{subject}"'
                    result, data = mail.search(None, search_criteria)
                    
                    if result == 'OK' and data[0]:
                        draft_count = len(data[0].split())
                        print(f"Found {draft_count} drafts matching subject '{subject}' in folder {folder}")
                        return True, folder
                    else:
                        print(f"No drafts found matching subject '{subject}' in folder {folder}")
                except Exception as e:
                    print(f"Error checking folder {folder}: {e}")
                    continue
            return False, None
        except Exception as e:
            print(f"Error verifying draft: {e}")
            return False, None

    def _get_latest_thread_info(self, thread_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure we have the latest message's thread info for proper threading.
        If thread_info has a message_id but no thread_history, fetch the thread.
        """
        if not thread_info:
            return {}
            
        # If we already have full thread history, use the latest message
        if thread_info.get('thread_messages') and len(thread_info['thread_messages']) > 0:
            # Sort messages by date and get the latest one
            sorted_msgs = sorted(
                thread_info['thread_messages'],
                key=lambda x: email.utils.parsedate_to_datetime(x['date']) if x.get('date') else datetime.datetime.min,
                reverse=True
            )
            latest = sorted_msgs[0]
            return {
                'message_id': latest.get('message_id', ''),
                'references': thread_info.get('references', ''),
                'in_reply_to': latest.get('message_id', ''),
                'date': latest.get('date', ''),
                'email_id': thread_info.get('email_id', '')
            }
        
        # If we only have a single message_id, use that
        return thread_info

    def _run(self, subject: str, body: str, recipient: str, thread_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a draft email to Gmail Drafts folder.
        """
        try:
            mail, email_address = self._connect()
            
            # Check available drafts folders
            drafts_folders = self._check_drafts_folder(mail)
            print(f"Available drafts folders: {drafts_folders}")
            
            # Try with quoted folder name first
            drafts_folder = '"[Gmail]/Drafts"'
            print(f"Selecting drafts folder: {drafts_folder}")
            result, _ = mail.select(drafts_folder)
            
            # If that fails, try without quotes
            if result != 'OK':
                drafts_folder = '[Gmail]/Drafts'
                print(f"First attempt failed. Trying: {drafts_folder}")
                result, _ = mail.select(drafts_folder)
            
            # If that also fails, try just 'Drafts'
            if result != 'OK':
                drafts_folder = 'Drafts'
                print(f"Second attempt failed. Trying: {drafts_folder}")
                result, _ = mail.select(drafts_folder)
            
            if result != 'OK':
                return f"Error: Could not select drafts folder. Available folders: {drafts_folders}"
                
            print(f"Successfully selected drafts folder: {drafts_folder}")
            
            # Format body and add signature
            body_with_signature = self._format_body(body)
            message = email.message.EmailMessage()
            message["From"] = email_address
            message["To"] = recipient

            # --- Robust subject handling for threading and Gmail compatibility ---
            thread_subject = None
            if thread_info:
                thread_subject = thread_info.get('thread_subject') or None
                # Try to extract from thread_messages if not present
                if not thread_subject and thread_info.get('thread_messages'):
                    for msg in thread_info['thread_messages']:
                        if msg.get('subject'):
                            thread_subject = msg['subject']
                            break

            # Gmail threading: If original subject is missing, use "Re: " only if replying, else "No Subject"
            if not subject or subject.strip() == "":
                if thread_subject and thread_subject.strip():
                    subject = thread_subject.strip()
                elif thread_info:
                    subject = "Re: No Subject"
                else:
                    subject = "No Subject"

            # Always ensure subject is prefixed with "Re: " for replies
            if thread_info and not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"

            message["Subject"] = subject

            # --- Always set threading headers if replying ---
            if thread_info:
                latest_thread_info = self._get_latest_thread_info(thread_info)
                references = []
                if latest_thread_info.get('references'):
                    references.extend(latest_thread_info['references'].split())
                if latest_thread_info.get('message_id'):
                    if latest_thread_info['message_id'] not in references:
                        references.append(latest_thread_info['message_id'])
                if references:
                    message["References"] = " ".join(references)
                if latest_thread_info.get('message_id'):
                    message["In-Reply-To"] = latest_thread_info['message_id']

            message.set_content(body_with_signature)

            # Save to drafts
            print(f"Attempting to save draft to {drafts_folder}...")
            date = imaplib.Time2Internaldate(time.time())
            result, data = mail.append(drafts_folder, '\\Draft', date, message.as_bytes())
            
            if result != 'OK':
                return f"Error saving draft: {result}, {data}"
            
            print(f"Draft save attempt result: {result}")
            
            # Verify the draft was actually saved
            verified, folder = self._verify_draft_saved(mail, subject, recipient)
            
            if verified:
                return f"VERIFIED: Draft email saved with subject: '{subject}' in folder {folder}"
            else:
                # Try Gmail's API approach as a fallback
                try:
                    # Try saving directly to All Mail and flagging as draft
                    result, data = mail.append('[Gmail]/All Mail', '\\Draft', date, message.as_bytes())
                    if result == 'OK':
                        return f"Draft saved to All Mail with subject: '{subject}' (flagged as draft)"
                    else:
                        return f"WARNING: Draft save attempt returned {result}, but verification failed. Please check your Gmail Drafts folder."
                except Exception as e:
                    return f"WARNING: Draft may not have been saved properly: {str(e)}"
        except Exception as e:
            return f"Error saving draft: {str(e)}"
        finally:
            self._disconnect(mail)

# -------------------------------
# Organize Email Tool
# -------------------------------

class GmailOrganizeSchema(BaseModel):
    """Schema for GmailOrganizeTool input."""
    email_id: str = Field(..., description="Email ID to organize")
    category: str = Field(..., description="Category assigned by agent (Urgent/Response Needed/etc)")
    priority: str = Field(..., description="Priority level (High/Medium/Low)")
    should_star: bool = Field(default=False, description="Whether to star the email")
    labels: List[str] = Field(default_list=[], description="Labels to apply")

class GmailOrganizeTool(GmailToolBase):
    """Tool to organize emails based on agent categorization."""
    name: str = "organize_email"
    description: str = "Organizes emails using Gmail's priority features based on category and priority"
    args_schema: Type[BaseModel] = GmailOrganizeSchema

    def _run(self, email_id: str, category: str, priority: str, should_star: bool = False, labels: List[str] = None) -> str:
        """
        Organize an email with the specified parameters.
        """
        if labels is None:
            # Provide a default empty list to avoid validation errors
            labels = []
        print(f"Organizing email {email_id} with category {category}, priority {priority}, star={should_star}, labels={labels}")
        
        mail = self._connect()
        try:
            # Select inbox to ensure we can access the email
            mail.select("INBOX")
            
            # Apply organization based on category and priority
            if category == "Urgent Response Needed" and priority == "High":
                # Star the email
                if should_star:
                    mail.store(email_id, '+FLAGS', '\\Flagged')
                
                # Mark as important
                mail.store(email_id, '+FLAGS', '\\Important')
                
                # Apply URGENT label if it doesn't exist
                if "URGENT" not in labels:
                    labels.append("URGENT")

            # Apply all specified labels
            for label in labels:
                try:
                    # Create label if it doesn't exist
                    mail.create(label)
                except:
                    pass  # Label might already exist
                
                # Apply label
                mail.store(email_id, '+X-GM-LABELS', label)

            return f"Email organized: Starred={should_star}, Labels={labels}"

        except Exception as e:
            return f"Error organizing email: {e}"
        finally:
            self._disconnect(mail)

# -------------------------------
# Delete Email Tool
# -------------------------------

class GmailDeleteSchema(BaseModel):
    """Schema for GmailDeleteTool input."""
    email_id: str = Field(..., description="Email ID to delete")
    reason: str = Field(..., description="Reason for deletion")

class GmailDeleteTool(BaseTool):
    """Tool to delete an email using IMAP."""
    name: str = "delete_email"
    description: str = "Deletes an email from Gmail"

    def _run(self, email_id: str, reason: str) -> str:
        """
        Delete an email by ID.
        Parameters:
            email_id: The email ID to delete
            reason: The reason for deletion (for logging)
        """
        try:
            # Validate inputs - Add this validation
            if not email_id or not isinstance(email_id, str):
                return f"Error: Invalid email_id format: {email_id}"
            if not reason or not isinstance(reason, str):
                return f"Error: Invalid reason format: {reason}"
            
            mail = self._connect()
            try:
                mail.select("INBOX")
                
                # First verify the email exists and get its details for logging
                result, data = mail.fetch(email_id, "(RFC822)")
                if result != "OK" or not data or data[0] is None:
                    return f"Error: Email with ID {email_id} not found"
                    
                msg = email.message_from_bytes(data[0][1])
                subject = decode_header_safe(msg["Subject"])
                sender = decode_header_safe(msg["From"])
                
                # Move to Trash
                mail.store(email_id, '+X-GM-LABELS', '\\Trash')
                mail.store(email_id, '-X-GM-LABELS', '\\Inbox')
                
                return f"Email deleted: '{subject}' from {sender}. Reason: {reason}"
            except Exception as e:
                return f"Error deleting email: {e}"
            finally:
                self._disconnect(mail)

        except Exception as e:
            return f"Error deleting email: {str(e)}"

# -------------------------------
# Empty Trash Tool
# -------------------------------

class EmptyTrashTool(BaseTool):
    """Tool to empty Gmail trash."""
    name: str = "empty_gmail_trash"
    description: str = "Empties the Gmail trash folder to free up space"

    def _connect(self):
        """Connect to Gmail using IMAP."""
        # Get email credentials from environment
        email_address = os.environ.get('EMAIL_ADDRESS')
        app_password = os.environ.get('APP_PASSWORD')
        
        if not email_address or not app_password:
            raise ValueError("EMAIL_ADDRESS or APP_PASSWORD environment variables not set")
        
        # Connect to Gmail's IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        print(f"Connecting to Gmail with email: {email_address[:3]}...{email_address[-10:]}")
        mail.login(email_address, app_password)
        return mail

    def _disconnect(self, mail):
        """Disconnect from Gmail."""
        try:
            mail.logout()
        except:
            pass
    
    def _run(self) -> str:
        """
        Empty the Gmail trash folder.
        """
        try:
            mail = self._connect()
            
            # Try different trash folder names (Gmail can have different naming conventions)
            trash_folders = [
                '"[Gmail]/Trash"',
                '[Gmail]/Trash',
                'Trash',
                '"[Google Mail]/Trash"',
                '[Google Mail]/Trash'
            ]
            success = False
            trash_folder_used = None
            
            for folder in trash_folders:
                try:
                    print(f"Attempting to select trash folder: {folder}")
                    result, data = mail.select(folder)
                    if result == 'OK':
                        trash_folder_used = folder
                        print(f"Successfully selected trash folder: {folder}")
                        
                        # Search for all messages in trash
                        result, data = mail.search(None, 'ALL')
                        
                        if result == 'OK':
                            email_ids = data[0].split()
                            count = len(email_ids)
                            if count == 0:
                                print("No messages found in trash.")
                                return "Trash is already empty. No messages to delete."
                            print(f"Found {count} messages in trash.")
                            
                            # Delete all messages in trash
                            for email_id in email_ids:
                                mail.store(email_id, '+FLAGS', '\\Deleted')
                            
                            # Permanently remove messages marked for deletion
                            mail.expunge()
                            success = True
                            break
                        
                except Exception as e:
                    print(f"Error accessing trash folder {folder}: {e}")
                    continue
            if success:
                return f"Successfully emptied Gmail trash folder ({trash_folder_used}). Deleted {count} messages."
            else:
                return "Could not empty trash. No trash folder found or accessible."

        except Exception as e:
            return f"Error emptying trash: {str(e)}"
        finally:
            self._disconnect(mail)

# -------------------------------
# Thread History Tool
# -------------------------------

class ThreadHistorySchema(BaseModel):
    """Schema for GetThreadHistoryTool input."""
    email_id: str = Field(..., description="Email ID to get the thread history for")
    include_attachments: bool = Field(
        default=False, 
        description="Whether to include information about attachments in the history"
    )
    max_depth: Optional[int] = Field(
        default=10, 
        description="Maximum number of emails to retrieve in the thread history",
        ge=1
    )

class GetThreadHistoryTool(GmailToolBase):
    """Tool to retrieve the complete history of an email thread."""
    name: str = "get_thread_history"
    description: str = "Gets the complete conversation history for an email thread"
    args_schema: Type[BaseModel] = ThreadHistorySchema
    
    def _run(self, email_id: str, include_attachments: bool = False, max_depth: int = 10) -> Dict[str, Any]:
        """
        Fetch the complete history of an email thread.

        Args:
            email_id: The email ID to get thread history for
            include_attachments: Whether to include attachment info
            max_depth: Maximum number of emails to retrieve

        Returns:
            A dictionary containing the thread history and metadata
        """
        mail = self._connect()
        try:
            mail.select("INBOX")
            
            # Fetch the target email first
            result, data = mail.fetch(email_id, "(RFC822)")
            if result != "OK":
                return {"error": f"Failed to fetch email with ID {email_id}"}
                
            raw_email = data[0][1]
            root_msg = email.message_from_bytes(raw_email)
            
            # Extract the Message-ID, References, and In-Reply-To
            message_id = root_msg.get("Message-ID", "").strip()
            references = root_msg.get("References", "").strip().split()
            in_reply_to = root_msg.get("In-Reply-To", "").strip()
            
            # Collect all relevant message IDs for the thread
            thread_ids = set()
            if message_id:
                thread_ids.add(message_id)
            if in_reply_to:
                thread_ids.add(in_reply_to)
            thread_ids.update(references)
            
            # Remove any empty strings
            thread_ids = {tid for tid in thread_ids if tid}
            print(f"Found {len(thread_ids)} related message IDs in thread")
            
            # Now search for all emails in this thread
            thread_messages = []
            thread_messages.append(self._process_message(root_msg, include_attachments))
            
            if thread_ids:
                # Build search query for all messages in thread
                search_terms = []
                for tid in thread_ids:
                    # Search by header field
                    search_terms.append(f'HEADER Message-ID "{tid}"')
                    search_terms.append(f'HEADER References "{tid}"')
                    search_terms.append(f'HEADER In-Reply-To "{tid}"')
                
                search_query = ' OR '.join(search_terms)
                
                # Execute the search
                result, data = mail.search(None, search_query)
                if result == "OK" and data[0]:
                    found_ids = data[0].split()
                    print(f"Found {len(found_ids)} emails in thread")
                    
                    # Limit to max_depth
                    if len(found_ids) > max_depth:
                        found_ids = found_ids[:max_depth]
                    
                    # Process each message
                    for msg_id in found_ids:
                        # Skip the root message as we already processed it
                        if msg_id.decode('utf-8') == email_id:
                            continue
                        result, msg_data = mail.fetch(msg_id, "(RFC822)")
                        if result == "OK":
                            msg = email.message_from_bytes(msg_data[0][1])
                            thread_messages.append(self._process_message(msg, include_attachments))
            
            # Sort messages by date
            thread_messages.sort(key=lambda x: email.utils.parsedate_to_datetime(x['date']) 
                               if x.get('date') and email.utils.parsedate_to_datetime(x['date']) 
                               else datetime.datetime.min)
            
            # Create a dictionary with thread info and messages
            thread_history = {
                "thread_messages": thread_messages,
                "message_count": len(thread_messages),
                "thread_subject": decode_header_safe(root_msg["Subject"]),
                "latest_message_id": message_id,
                "participants": self._extract_participants(thread_messages)
            }
            return thread_history
            
        except Exception as e:
            print(f"Error retrieving thread history: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        finally:
            self._disconnect(mail)

    def _process_message(self, msg, include_attachments: bool) -> Dict[str, Any]:
        """
        Process an email message into a structured format.
        """
        # Extract headers
        subject = decode_header_safe(msg["Subject"])
        sender = decode_header_safe(msg["From"])
        to = decode_header_safe(msg["To"])
        date = msg["Date"]
        message_id = msg.get("Message-ID", "")
        in_reply_to = msg.get("In-Reply-To", "")
        references = msg.get("References", "")
        
        # Extract body
        body = self._extract_body(msg)
        
        # Process attachments if requested
        attachments = []
        if include_attachments and msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": decode_header_safe(filename),
                            "type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })
        
        # Create message dict
        message_dict = {
            "subject": subject,
            "sender": sender,
            "to": to,
            "date": date,
            "body": body,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references
        }
        if include_attachments:
            message_dict["attachments"] = attachments
        return message_dict

    def _extract_participants(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Extract all unique participants from the thread.
        """
        participants = set()
        for msg in messages:
            # Extract email addresses from sender and recipient fields
            for field in ['sender', 'to', 'cc', 'bcc']:
                if field in msg and msg[field]:
                    # Use regex to extract email addresses
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+', msg[field])
                    participants.update(emails)
        return list(participants)

# -------------------------------
# Context-Aware Reply Tool
# -------------------------------

class ContextAwareReplySchema(BaseModel):
    """Schema for ContextAwareReplyTool input."""
    email_id: str = Field(..., description="Email ID to reply to")
    subject: Optional[str] = Field(None, description="Optional subject override")
    body: str = Field(..., description="Reply body content")
    include_history: bool = Field(default=True, description="Whether to include conversation history when drafting")
    max_history_depth: int = Field(default=5, description="Maximum number of emails to include in history")

class ContextAwareReplyTool(GmailToolBase):
    """Tool to draft replies with full conversation context."""
    name: str = "draft_contextual_reply"
    description: str = "Drafts a reply with full conversation context"
    args_schema: Type[BaseModel] = ContextAwareReplySchema
    
    def _run(self, email_id: str, body: str, subject: Optional[str] = None, 
             include_history: bool = True, max_history_depth: int = 5) -> str:
        """
        Draft a reply to an email with full conversation context.
        """
        mail = self._connect()
        try:
            # Fetch the email to reply to
            result, data = mail.fetch(email_id, "(RFC822)")
            if result != "OK":
                return f"Failed to fetch email with ID {email_id}"
                
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract key information
            original_subject = decode_header_safe(msg["Subject"])
            sender = decode_header_safe(msg["From"])
            reply_to = msg.get("Reply-To", sender)
            
            # Extract email address from the sender/reply-to field
            recipient_match = re.search(r'<([^>]+)>', reply_to)
            if recipient_match:
                recipient = recipient_match.group(1)
            else:
                recipient = reply_to
            
            # Set subject (add Re: if needed)
            if subject is None or subject.strip() == "":
                if not original_subject or original_subject.strip() == "":
                    subject = "Re: No Subject"
                elif not original_subject.lower().startswith('re:'):
                    subject = f"Re: {original_subject}"
                else:
                    subject = original_subject
            
            # Get thread history if requested
            thread_info = {
                'message_id': msg.get('Message-ID', ''),
                'in_reply_to': msg.get('In-Reply-To', ''),
                'references': msg.get('References', ''),
                'email_id': email_id
            }
            
            if include_history:
                # Fetch thread history
                thread_history_tool = GetThreadHistoryTool()
                thread_history = thread_history_tool._run(
                    email_id=email_id,
                    include_attachments=True,
                    max_depth=max_history_depth
                )
                
                # Add thread history to thread_info
                thread_info['thread_messages'] = thread_history.get('thread_messages', [])
                thread_info['thread_subject'] = thread_history.get('thread_subject', '')
                thread_info['participants'] = thread_history.get('participants', [])
            
            # Use SaveDraftTool to save the draft
            draft_tool = SaveDraftTool()
            result = draft_tool._run(
                subject=subject,
                body=body,
                recipient=recipient,
                thread_info=thread_info
            )
            
            return result
            
        except Exception as e:
            print(f"Error creating contextual reply: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
        finally:
            self._disconnect(mail)

# -------------------------------
# Gmail API Integration
# -------------------------------

class GmailReader(BaseTool):
    name: str = "Gmail Reader"
    description: str = "Reads emails from Gmail, specifically looking for ServiceNow notifications and incident reports"

    def _run(self, query: str = "", max_results: int = 10) -> str:
        """
        Read emails from Gmail with focus on ServiceNow emails
        """
        try:
            # This would integrate with Gmail API
            # For now, returning mock ServiceNow email data
            servicenow_emails = [
                {
                    "id": "email_001",
                    "subject": "INC0123456 - Network connectivity issue - Assigned to you",
                    "from": "servicenow@company.com",
                    "body": """
                    Incident Number: INC0123456
                    State: Assigned
                    Priority: P2 - High
                    Category: Network
                    Short Description: Network connectivity issue in Building A
                    Assigned to: John Doe
                    Reporter: Jane Smith
                    
                    Please investigate the network connectivity issues reported in Building A.
                    Users are unable to access internal systems.
                    """,
                    "received_time": "2024-01-15 10:30:00"
                },
                {
                    "id": "email_002", 
                    "subject": "REQ0087654 - Software installation request - Pending approval",
                    "from": "servicenow@company.com",
                    "body": """
                    Request Number: REQ0087654
                    State: Pending Approval
                    Category: Software
                    Short Description: Install Adobe Creative Suite
                    Requested by: Mike Johnson
                    Approver: IT Manager
                    
                    Please review and approve the software installation request.
                    """,
                    "received_time": "2024-01-15 11:15:00"
                }
            ]
            
            return json.dumps(servicenow_emails, indent=2)
            
        except Exception as e:
            return f"Error reading emails: {str(e)}"

class ServiceNowEmailParser(BaseTool):
    name: str = "ServiceNow Email Parser"
    description: str = "Parses ServiceNow emails to extract ticket information, status, and context"

    def _run(self, email_content: str) -> str:
        """
        Parse ServiceNow email content to extract relevant information
        """
        try:
            # Parse email content using BeautifulSoup for HTML emails
            soup = BeautifulSoup(email_content, 'html.parser')
            text_content = soup.get_text() if soup else email_content
            
            # Extract key ServiceNow information
            parsed_info = {
                "ticket_number": self._extract_ticket_number(text_content),
                "ticket_type": self._extract_ticket_type(text_content),
                "state": self._extract_state(text_content),
                "priority": self._extract_priority(text_content),
                "category": self._extract_category(text_content),
                "short_description": self._extract_description(text_content),
                "assigned_to": self._extract_assigned_to(text_content),
                "reporter": self._extract_reporter(text_content),
                "urgency": self._extract_urgency(text_content)
            }
            
            return json.dumps(parsed_info, indent=2)
            
        except Exception as e:
            return f"Error parsing ServiceNow email: {str(e)}"
    
    def _extract_ticket_number(self, text: str) -> Optional[str]:
        """Extract ticket number (INC, REQ, CHG, etc.)"""
        patterns = [
            r'(INC\d{7})',
            r'(REQ\d{7})',
            r'(CHG\d{7})',
            r'(RITM\d{7})',
            r'Incident Number:\s*([A-Z]{3}\d{7})',
            r'Request Number:\s*([A-Z]{3}\d{7})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_ticket_type(self, text: str) -> Optional[str]:
        """Determine ticket type based on number prefix"""
        ticket_num = self._extract_ticket_number(text)
        if ticket_num:
            if ticket_num.startswith('INC'):
                return 'Incident'
            elif ticket_num.startswith('REQ') or ticket_num.startswith('RITM'):
                return 'Request'
            elif ticket_num.startswith('CHG'):
                return 'Change'
        return None
    
    def _extract_state(self, text: str) -> Optional[str]:
        """Extract current state/status"""
        patterns = [
            r'State:\s*([^\\n]+)',
            r'Status:\s*([^\\n]+)',
            r'Current State:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority level"""
        patterns = [
            r'Priority:\s*([^\\n]+)',
            r'Priority Level:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_category(self, text: str) -> Optional[str]:
        """Extract category"""
        patterns = [
            r'Category:\s*([^\\n]+)',
            r'Service Category:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract short description"""
        patterns = [
            r'Short Description:\s*([^\\n]+)',
            r'Description:\s*([^\\n]+)',
            r'Summary:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_assigned_to(self, text: str) -> Optional[str]:
        """Extract assigned person"""
        patterns = [
            r'Assigned to:\s*([^\\n]+)',
            r'Assignee:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_reporter(self, text: str) -> Optional[str]:
        """Extract reporter/requester"""
        patterns = [
            r'Reporter:\s*([^\\n]+)',
            r'Requested by:\s*([^\\n]+)',
            r'Caller:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_urgency(self, text: str) -> Optional[str]:
        """Extract urgency level"""
        patterns = [
            r'Urgency:\s*([^\\n]+)',
            r'Urgency Level:\s*([^\\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

class ServiceNowResponseGenerator(BaseTool):
    name: str = "ServiceNow Response Generator"
    description: str = "Generates appropriate responses for different types of ServiceNow emails"

    def _run(self, ticket_info: str, response_type: str = "acknowledgment") -> str:
        """
        Generate contextual responses based on ServiceNow ticket information
        """
        try:
            ticket_data = json.loads(ticket_info)
            ticket_type = ticket_data.get('ticket_type', 'Unknown')
            state = ticket_data.get('state', 'Unknown')
            priority = ticket_data.get('priority', 'Unknown')
            ticket_number = ticket_data.get('ticket_number', 'Unknown')
            
            responses = {
                "acknowledgment": self._generate_acknowledgment(ticket_data),
                "status_update": self._generate_status_update(ticket_data),
                "resolution": self._generate_resolution(ticket_data),
                "escalation": self._generate_escalation(ticket_data),
                "approval_request": self._generate_approval_request(ticket_data)
            }
            
            return responses.get(response_type, self._generate_acknowledgment(ticket_data))
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _generate_acknowledgment(self, ticket_data: Dict) -> str:
        """Generate acknowledgment response"""
        ticket_number = ticket_data.get('ticket_number', 'Unknown')
        ticket_type = ticket_data.get('ticket_type', 'ticket')
        priority = ticket_data.get('priority', 'Unknown')
        
        return f"""
Subject: Re: {ticket_number} - Acknowledgment

Dear Team,

I have received the {ticket_type.lower()} {ticket_number} notification.

Ticket Details:
- Priority: {priority}
- Current Status: {ticket_data.get('state', 'Unknown')}
- Category: {ticket_data.get('category', 'Unknown')}

I will review this {ticket_type.lower()} and provide updates as needed. 
If this is urgent, please feel free to reach out directly.

Best regards,
[Your Name]
        """.strip()
    
    def _generate_status_update(self, ticket_data: Dict) -> str:
        """Generate status update response"""
        ticket_number = ticket_data.get('ticket_number', 'Unknown')
        
        return f"""
Subject: Re: {ticket_number} - Status Update

Dear Team,

Status update for {ticket_number}:

I am currently working on this issue and have identified the following:
- Initial assessment completed
- Root cause analysis in progress
- Expected resolution timeframe: [To be determined based on investigation]

I will provide another update within [timeframe] or sooner if significant progress is made.

Best regards,
[Your Name]
        """.strip()
    
    def _generate_resolution(self, ticket_data: Dict) -> str:
        """Generate resolution response"""
        ticket_number = ticket_data.get('ticket_number', 'Unknown')
        
        return f"""
Subject: Re: {ticket_number} - Resolution Provided

Dear Team,

I have resolved {ticket_number}. 

Resolution Summary:
- Issue has been addressed
- Solution implemented and tested
- Normal operations restored

Please verify the resolution and close the ticket if everything is working as expected.
If you experience any further issues, please don't hesitate to reopen this ticket.

Best regards,
[Your Name]
        """.strip()
    
    def _generate_escalation(self, ticket_data: Dict) -> str:
        """Generate escalation response"""
        ticket_number = ticket_data.get('ticket_number', 'Unknown')
        priority = ticket_data.get('priority', 'Unknown')
        
        return f"""
Subject: Re: {ticket_number} - Escalation Required

Dear Manager,

I need to escalate {ticket_number} due to:
- Priority: {priority}
- Complexity beyond current skill level / Additional resources required
- Time constraints / SLA concerns

Current Status:
- Actions taken: [Summary of work performed]
- Blockers: [Specific challenges encountered]
- Recommendation: [Suggested next steps]

Please advise on the appropriate escalation path.

Best regards,
[Your Name]
        """.strip()
    
    def _generate_approval_request(self, ticket_data: Dict) -> str:
        """Generate approval request response"""
        ticket_number = ticket_data.get('ticket_number', 'Unknown')
        
        return f"""
Subject: Re: {ticket_number} - Approval Decision

Dear Requester,

Regarding {ticket_number}:

After reviewing the request details, I am [approving/rejecting/requesting more information for] this request.

[If approved:]
The request has been approved and will proceed to fulfillment.

[If rejected:]
The request has been rejected for the following reasons:
- [Reason 1]
- [Reason 2]

[If more info needed:]
Additional information is required before processing:
- [Information needed]

Please let me know if you have any questions.

Best regards,
[Your Name]
        """.strip()

class GmailSender(BaseTool):
    name: str = "Gmail Sender"
    description: str = "Sends generated responses via Gmail"

    def _run(self, to_email: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
        """
        Send email response via Gmail API
        """
        try:
            # This would integrate with Gmail API to actually send emails
            # For now, returning confirmation message
            
            email_details = {
                "to": to_email,
                "subject": subject,
                "body": body,
                "cc": cc,
                "bcc": bcc,
                "status": "sent",
                "timestamp": "2024-01-15 12:00:00"
            }
            
            return f"Email sent successfully: {json.dumps(email_details, indent=2)}"
            
        except Exception as e:
            return f"Error sending email: {str(e)}"