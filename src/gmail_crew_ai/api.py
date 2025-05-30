from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import json
from gmail_crew_ai.tools.gmail_tools import (
    fetch_unread_emails,
    save_email_draft,
    mark_email_as_read
)
from pathlib import Path
import os

app = FastAPI(title="Gmail & ServiceNow Automation API")

# Ensure output directory exists
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

class EmailRequest(BaseModel):
    max_emails: int = 10

class DraftRequest(BaseModel):
    subject: str
    body: str
    recipient: str
    thread_info: dict = None

@app.get("/")
def read_root():
    return {"message": "Gmail and ServiceNow Automation API is running"}

@app.post("/fetch-emails")
async def fetch_emails(request: EmailRequest, background_tasks: BackgroundTasks):
    try:
        emails = fetch_unread_emails(max_emails=request.max_emails)
        
        # Save emails to a JSON file
        with open(output_dir / "fetched_emails.json", "w") as f:
            json.dump(emails, f, indent=2)
        
        return {"status": "success", "message": f"Fetched {len(emails)} emails", "emails": emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.post("/save-draft")
async def save_draft(request: DraftRequest):
    try:
        result = save_email_draft(
            subject=request.subject,
            body=request.body,
            recipient=request.recipient,
            thread_info=request.thread_info
        )
        return {"status": "success", "message": "Draft saved successfully", "draft_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving draft: {str(e)}")

@app.post("/mark-as-read/{email_id}")
async def mark_as_read(email_id: str):
    try:
        mark_email_as_read(email_id)
        return {"status": "success", "message": f"Email {email_id} marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking email as read: {str(e)}")
