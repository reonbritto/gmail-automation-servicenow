from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from gmail_crew_ai.tools.gmail_tools import (
    GetUnreadEmailsTool,
    GetThreadHistoryTool,
    ContextAwareReplyTool,
)
from gmail_crew_ai.crew import GmailCrewAi

# Create FastAPI app with metadata
app = FastAPI(
    title="Gmail CrewAI API",
    description="API for email automation with AI-powered assistants",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

class ReplyRequest(BaseModel):
    email_id: str
    body: str
    subject: Optional[str] = None
    include_history: bool = True
    max_history_depth: int = 5
    
    class Config:
        schema_extra = {
            "example": {
                "email_id": "12345",
                "body": "Thank you for your email. I'll review your proposal and get back to you soon.",
                "subject": "Re: Your Project Proposal",
                "include_history": True,
                "max_history_depth": 5
            }
        }

@app.get("/")
def root():
    """
    Gmail CrewAI API - Email automation with AI.
    
    This API provides endpoints to:
    - Fetch unread emails
    - Retrieve email thread history
    - Draft context-aware replies
    - Run the full email automation crew
    
    For complete documentation with examples, visit /docs
    """
    return {
        "name": "Gmail CrewAI API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/emails/unread", "method": "GET", "description": "Fetch unread emails"},
            {"path": "/emails/thread-history", "method": "GET", "description": "Get thread history"},
            {"path": "/emails/draft-reply", "method": "POST", "description": "Draft a reply"},
            {"path": "/crew/run", "method": "POST", "description": "Run full automation"}
        ],
        "documentation_url": "/docs"
    }

@app.get("/emails/unread")
def get_unread_emails(limit: int = Query(5, ge=1, le=50, description="Maximum number of emails to fetch")):
    """
    Fetch unread emails from your Gmail inbox.
    
    Parameters:
    - **limit**: Maximum number of unread emails to retrieve (1-50)
    
    Returns a list of unread emails with their details.
    """
    tool = GetUnreadEmailsTool()
    emails = tool._run(limit=limit)
    return {"emails": emails}

@app.get("/emails/thread-history")
def get_thread_history(
    email_id: str = Query(..., description="Email ID to get thread history for"),
    include_attachments: bool = Query(False, description="Include attachment information"),
    max_depth: int = Query(10, ge=1, le=50, description="Maximum emails to include in history")
):
    """
    Get complete conversation history for an email thread.
    
    Parameters:
    - **email_id**: ID of the email (required)
    - **include_attachments**: Whether to include attachment information
    - **max_depth**: Maximum number of emails to retrieve in the thread
    
    Returns the complete thread history with all messages in chronological order.
    """
    tool = GetThreadHistoryTool()
    history = tool._run(email_id=email_id, include_attachments=include_attachments, max_depth=max_depth)
    return history

@app.post("/emails/draft-reply")
def draft_contextual_reply(request: ReplyRequest):
    """
    Draft a context-aware reply to an email.
    
    The reply will be saved as a draft in your Gmail account. Gmail's threading
    features will ensure it appears correctly in the conversation.
    
    Parameters:
    - **email_id**: ID of the email to reply to
    - **body**: Content of your reply
    - **subject**: Optional subject override
    - **include_history**: Whether to fetch and include conversation history
    - **max_history_depth**: Maximum emails to include in history context
    
    Returns the result of the draft creation operation.
    """
    tool = ContextAwareReplyTool()
    result = tool._run(
        email_id=request.email_id,
        body=request.body,
        subject=request.subject,
        include_history=request.include_history,
        max_history_depth=request.max_history_depth,
    )
    return {"result": result}

@app.post("/crew/run")
def run_crew(email_limit: int = Query(5, ge=1, le=20, description="Number of emails to process")):
    """
    Run the full email processing crew with AI agents.
    
    This endpoint triggers the complete workflow:
    1. Fetches unread emails
    2. Analyzes each email
    3. Determines which emails need responses
    4. Drafts appropriate replies
    
    Parameters:
    - **email_limit**: Number of unread emails to process
    
    Returns the results of the crew execution.
    
    Note: This operation may take some time to complete depending on the
    number of emails being processed.
    """
    result = GmailCrewAi().crew().kickoff(inputs={'email_limit': email_limit})
    return {"result": result}
