from datetime import datetime, date, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import re
import time

class DateCalculationSchema(BaseModel):
    """Schema for DateCalculationTool input."""
    email_date: str = Field(..., description="Email date in ISO format (YYYY-MM-DD)")
    # Remove reference_date from schema to prevent agent from using it
    # reference_date: Optional[str] = Field(None, description="Reference date in ISO format (YYYY-MM-DD). Defaults to today.")

class DateCalculationTool(BaseTool):
    """Tool to calculate the age of an email in days."""
    name: str = "calculate_email_age"
    description: str = "Calculate how many days old an email is compared to today's date"
    args_schema: type[BaseModel] = DateCalculationSchema

    def _run(self, email_date: str, reference_date: Optional[str] = None) -> str:
        """Calculate the age of an email in days compared to today.
        
        Args:
            email_date: The date of the email in YYYY-MM-DD format
            
        Returns:
            A string with the email age information
        """
        try:
            # Parse the email date
            email_date_obj = datetime.strptime(email_date, "%Y-%m-%d").date()
            
            # Always use today's date - ignore any provided reference_date
            today = date.today()
            
            # Calculate the age in days
            age_days = (today - email_date_obj).days
            
            # Create the response
            response = f"Email age: {age_days} days from today ({today})\n"
            response += f"Email date: {email_date_obj}\n"
            response += f"- Less than 5 days old: {'Yes' if age_days < 5 else 'No'}\n"
            response += f"- Older than 7 days: {'Yes' if age_days > 7 else 'No'}\n"
            response += f"- Older than 10 days: {'Yes' if age_days > 10 else 'No'}\n"
            response += f"- Older than 14 days: {'Yes' if age_days > 14 else 'No'}\n"
            response += f"- Older than 30 days: {'Yes' if age_days > 30 else 'No'}\n"
            
            return response
            
        except Exception as e:
            return f"Error calculating email age: {str(e)}"

class DateTimeHelper(BaseTool):
    name: str = "DateTime Helper"
    description: str = "Provides date and time utilities for email processing and ServiceNow ticket management"

    def _run(self, operation: str, date_string: str = "", format_type: str = "standard") -> str:
        """
        Perform date/time operations for email automation
        
        Operations:
        - current_time: Get current timestamp
        - parse_date: Parse date from string
        - calculate_sla: Calculate SLA deadlines
        - format_date: Format date for responses
        """
        try:
            if operation == "current_time":
                return self._get_current_time(format_type)
            elif operation == "parse_date":
                return self._parse_date(date_string)
            elif operation == "calculate_sla":
                return self._calculate_sla_deadline(date_string)
            elif operation == "format_date":
                return self._format_date_for_response(date_string)
            else:
                return "Invalid operation. Use: current_time, parse_date, calculate_sla, format_date"
                
        except Exception as e:
            return f"Error in date operation: {str(e)}"
    
    def _get_current_time(self, format_type: str = "standard") -> str:
        """Get current timestamp in various formats"""
        now = datetime.now()
        
        formats = {
            "standard": now.strftime("%Y-%m-%d %H:%M:%S"),
            "servicenow": now.strftime("%Y-%m-%d %H:%M:%S"),
            "email": now.strftime("%a, %d %b %Y %H:%M:%S"),
            "iso": now.isoformat(),
            "friendly": now.strftime("%B %d, %Y at %I:%M %p")
        }
        
        return formats.get(format_type, formats["standard"])
    
    def _parse_date(self, date_string: str) -> str:
        """Parse date from various string formats"""
        patterns = [
            ("%Y-%m-%d %H:%M:%S", "Standard format"),
            ("%Y-%m-%d", "Date only"),
            ("%m/%d/%Y", "US format"),
            ("%d/%m/%Y", "UK format"),
            ("%B %d, %Y", "Long format"),
            ("%b %d, %Y", "Short month format")
        ]
        
        for pattern, description in patterns:
            try:
                parsed_date = datetime.strptime(date_string, pattern)
                return f"Parsed date: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')} ({description})"
            except ValueError:
                continue
        
        return f"Could not parse date: {date_string}"
    
    def _calculate_sla_deadline(self, created_date: str, priority: str = "P3") -> str:
        """Calculate SLA deadline based on priority"""
        try:
            # Parse the creation date
            if not created_date:
                created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            creation_time = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
            
            # SLA hours based on priority
            sla_hours = {
                "P1": 4,    # Critical - 4 hours
                "P2": 24,   # High - 1 day
                "P3": 72,   # Medium - 3 days
                "P4": 168   # Low - 7 days
            }
            
            hours = sla_hours.get(priority, 72)  # Default to P3
            deadline = creation_time + timedelta(hours=hours)
            
            return f"SLA Deadline: {deadline.strftime('%Y-%m-%d %H:%M:%S')} ({hours} hours from creation)"
            
        except Exception as e:
            return f"Error calculating SLA: {str(e)}"
    
    def _format_date_for_response(self, date_string: str) -> str:
        """Format date for email responses"""
        try:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime("%B %d, %Y at %I:%M %p")
        except ValueError:
            return date_string

class BusinessHoursCalculator(BaseTool):
    name: str = "Business Hours Calculator"
    description: str = "Calculates business hours and working days for SLA management"

    def _run(self, start_date: str, end_date: str = "", operation: str = "business_hours") -> str:
        """
        Calculate business hours between dates or check if current time is business hours
        """
        try:
            if operation == "is_business_hours":
                return self._is_business_hours()
            elif operation == "business_hours_between":
                return self._calculate_business_hours(start_date, end_date)
            elif operation == "next_business_day":
                return self._next_business_day(start_date)
            else:
                return "Invalid operation. Use: is_business_hours, business_hours_between, next_business_day"
                
        except Exception as e:
            return f"Error in business hours calculation: {str(e)}"
    
    def _is_business_hours(self) -> str:
        """Check if current time is within business hours"""
        now = datetime.now()
        
        # Business hours: Monday-Friday, 9 AM - 5 PM
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return "Outside business hours (Weekend)"
        
        if now.hour < 9 or now.hour >= 17:
            return "Outside business hours (After hours)"
        
        return "Within business hours"
    
    def _calculate_business_hours(self, start_date: str, end_date: str) -> str:
        """Calculate business hours between two dates"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            
            business_hours = 0
            current = start
            
            while current < end:
                if current.weekday() < 5:  # Monday-Friday
                    if 9 <= current.hour < 17:  # Business hours
                        business_hours += 1
                current += timedelta(hours=1)
            
            return f"Business hours between dates: {business_hours} hours"
            
        except Exception as e:
            return f"Error calculating business hours: {str(e)}"
    
    def _next_business_day(self, date_string: str) -> str:
        """Get next business day"""
        try:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            
            # Add days until we reach a weekday
            while date_obj.weekday() >= 5:  # Saturday or Sunday
                date_obj += timedelta(days=1)
            
            return f"Next business day: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            return f"Error finding next business day: {str(e)}"