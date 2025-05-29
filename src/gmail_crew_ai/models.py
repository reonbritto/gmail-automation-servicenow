from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TicketType(str, Enum):
    INCIDENT = "Incident"
    REQUEST = "Request" 
    CHANGE = "Change"
    PROBLEM = "Problem"

class TicketState(str, Enum):
    NEW = "New"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"

class Priority(str, Enum):
    P1_CRITICAL = "P1 - Critical"
    P2_HIGH = "P2 - High"
    P3_MEDIUM = "P3 - Medium"
    P4_LOW = "P4 - Low"

class ServiceNowTicket(BaseModel):
    """Model for ServiceNow ticket information"""
    ticket_number: Optional[str] = Field(None, description="ServiceNow ticket number (e.g., INC0123456)")
    ticket_type: Optional[TicketType] = Field(None, description="Type of ServiceNow ticket")
    state: Optional[TicketState] = Field(None, description="Current state of the ticket")
    priority: Optional[Priority] = Field(None, description="Priority level")
    urgency: Optional[str] = Field(None, description="Urgency level")
    category: Optional[str] = Field(None, description="Service category")
    subcategory: Optional[str] = Field(None, description="Service subcategory")
    short_description: Optional[str] = Field(None, description="Brief description of the issue")
    detailed_description: Optional[str] = Field(None, description="Detailed description")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the ticket")
    assignment_group: Optional[str] = Field(None, description="Group assigned to the ticket")
    reporter: Optional[str] = Field(None, description="Person who reported the issue")
    created_date: Optional[datetime] = Field(None, description="When the ticket was created")
    updated_date: Optional[datetime] = Field(None, description="Last update time")
    sla_deadline: Optional[datetime] = Field(None, description="SLA deadline")
    resolution_notes: Optional[str] = Field(None, description="Resolution details")
    work_notes: List[str] = Field(default_factory=list, description="Work notes/comments")

class EmailContent(BaseModel):
    """Model for email content and metadata"""
    email_id: str = Field(..., description="Unique email identifier")
    subject: str = Field(..., description="Email subject line")
    sender: str = Field(..., description="Email sender address")
    recipients: List[str] = Field(default_factory=list, description="Email recipients")
    cc_recipients: List[str] = Field(default_factory=list, description="CC recipients")
    body_text: str = Field(..., description="Email body content")
    body_html: Optional[str] = Field(None, description="HTML email content")
    received_date: datetime = Field(..., description="When email was received")
    is_servicenow: bool = Field(False, description="Whether this is a ServiceNow email")
    attachments: List[str] = Field(default_factory=list, description="Attachment file names")

class ResponseType(str, Enum):
    ACKNOWLEDGMENT = "acknowledgment"
    STATUS_UPDATE = "status_update"
    RESOLUTION = "resolution"
    ESCALATION = "escalation"
    APPROVAL_REQUEST = "approval_request"
    INFORMATION_REQUEST = "information_request"
    CLOSURE_CONFIRMATION = "closure_confirmation"

class EmailResponse(BaseModel):
    """Model for generated email responses"""
    response_type: ResponseType = Field(..., description="Type of response being generated")
    subject: str = Field(..., description="Response email subject")
    body: str = Field(..., description="Response email body")
    recipients: List[str] = Field(..., description="Who should receive the response")
    cc_recipients: List[str] = Field(default_factory=list, description="CC recipients")
    priority: str = Field("Normal", description="Email priority")
    send_immediately: bool = Field(True, description="Whether to send immediately or queue")
    template_used: Optional[str] = Field(None, description="Response template used")

class WorkflowContext(BaseModel):
    """Model for workflow context and state"""
    email_content: EmailContent
    parsed_ticket: Optional[ServiceNowTicket] = None
    suggested_response: Optional[EmailResponse] = None
    workflow_stage: str = Field("email_received", description="Current workflow stage")
    processing_notes: List[str] = Field(default_factory=list, description="Processing notes")
    requires_human_review: bool = Field(False, description="Whether human review is needed")
    confidence_score: float = Field(0.0, description="AI confidence in the response (0-1)")

class AutomationSettings(BaseModel):
    """Model for automation configuration"""
    auto_send_threshold: float = Field(0.8, description="Confidence threshold for auto-sending")
    business_hours_only: bool = Field(True, description="Only process during business hours")
    max_daily_responses: int = Field(50, description="Maximum responses per day")
    excluded_senders: List[str] = Field(default_factory=list, description="Senders to ignore")
    priority_keywords: Dict[str, Priority] = Field(
        default_factory=lambda: {
            "urgent": Priority.P1_CRITICAL,
            "critical": Priority.P1_CRITICAL,
            "high": Priority.P2_HIGH,
            "important": Priority.P2_HIGH
        },
        description="Keywords that indicate priority"
    )
    category_mappings: Dict[str, str] = Field(
        default_factory=lambda: {
            "network": "Network",
            "hardware": "Hardware", 
            "software": "Software",
            "access": "Access Management",
            "email": "Email/Messaging"
        },
        description="Category keyword mappings"
    )

class ResponseTemplate(BaseModel):
    """Model for response templates"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    response_type: ResponseType = Field(..., description="Type of response this template is for")
    subject_template: str = Field(..., description="Subject line template with placeholders")
    body_template: str = Field(..., description="Email body template with placeholders")
    required_fields: List[str] = Field(default_factory=list, description="Required ticket fields")
    applicable_categories: List[str] = Field(default_factory=list, description="Applicable ticket categories")
    tone: str = Field("professional", description="Response tone (professional, friendly, formal)")
    
class ProcessingResult(BaseModel):
    """Model for workflow processing results"""
    success: bool = Field(..., description="Whether processing was successful")
    email_id: str = Field(..., description="Processed email ID")
    ticket_number: Optional[str] = Field(None, description="Associated ServiceNow ticket")
    response_sent: bool = Field(False, description="Whether response was sent")
    response_queued: bool = Field(False, description="Whether response was queued for review")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processing_time_seconds: float = Field(..., description="Time taken to process")
    human_review_required: bool = Field(False, description="Whether human review is needed")
    confidence_score: float = Field(0.0, description="Overall confidence in processing")

class EmailDetails(BaseModel):
    """Model for email details."""
    email_id: Optional[str] = Field(None, description="Email ID")
    subject: Optional[str] = Field(None, description="Email subject")
    sender: Optional[str] = Field(None, description="Email sender")
    body: Optional[str] = Field(None, description="Email body")
    date: Optional[str] = Field(None, description="Email date (YYYY-MM-DD)")
    age_days: Optional[int] = Field(None, description="Age of the email in days from today")
    thread_info: Optional[Dict[str, Any]] = Field(None, description="Thread information")
    is_part_of_thread: Optional[bool] = Field(False, description="Whether this email is part of a thread")
    thread_size: Optional[int] = Field(1, description="Number of emails in this thread")
    thread_position: Optional[int] = Field(1, description="Position of this email in the thread (1 = first)")

    @classmethod
    def from_email_tuple(cls, email_tuple):
        """Create an EmailDetails from an email tuple."""
        if not email_tuple or len(email_tuple) < 5:
            return cls(email_id=None, subject=None)
        
        subject, sender, body, email_id, thread_info = email_tuple
        
        # Extract date from thread_info
        date = ""
        if isinstance(thread_info, dict) and 'date' in thread_info:
            date = thread_info['date']
            
        return cls(
            email_id=email_id,
            subject=subject,
            sender=sender,
            body=body,
            date=date,
            thread_info=thread_info
        )

class EmailResponse(BaseModel):
    """Model for email response information."""
    email_id: str = Field(..., description="Unique identifier for the email")
    subject: str = Field(..., description="Email subject line")
    recipient: str = Field(..., description="Email recipient")
    response_summary: str = Field(..., description="Summary of the response")
    response_needed: bool = Field(..., description="Whether a response was needed")
    draft_saved: bool = Field(default=False, description="Whether a draft was saved")

class EmailResponseList(BaseModel):
    """Wrapper model for a list of email responses."""
    responses: List[EmailResponse] = Field(default_factory=list, description="List of email responses")
