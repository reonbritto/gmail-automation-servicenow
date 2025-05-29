import os
import json
from typing import Dict, Any, List
from datetime import datetime
from crewai_tools import BaseTool
from pydantic import BaseModel, Field

class EmailAnalysis(BaseModel):
    """Structure for email analysis results"""
    needs_response: bool = Field(description="Whether email requires a response")
    response_type: str = Field(description="Type of response needed")
    urgency: str = Field(description="Urgency level (high, medium, low)")
    key_points: List[str] = Field(description="Key points from the email")
    suggested_tone: str = Field(description="Suggested tone for response")

class EmailAnalysisTool(BaseTool):
    """Tool for analyzing emails to determine response requirements"""
    
    name: str = "Email Analysis Tool"
    description: str = "Analyzes email content to determine if a response is needed and what type"
    
    def _run(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email to determine response requirements
        
        Args:
            email_data: Dictionary containing email information
            
        Returns:
            Analysis results with response recommendations
        """
        try:
            subject = email_data.get("subject", "")
            sender = email_data.get("sender", "")
            body = email_data.get("body", "")
            is_servicenow = email_data.get("is_servicenow", False)
            priority = email_data.get("priority", "normal")
            
            # Determine if response is needed
            needs_response = self._needs_response(subject, sender, body, is_servicenow)
            
            # Determine response type
            response_type = self._determine_response_type(subject, body, is_servicenow)
            
            # Determine urgency
            urgency = self._determine_urgency(subject, body, priority, is_servicenow)
            
            # Extract key points
            key_points = self._extract_key_points(subject, body)
            
            # Suggest tone
            suggested_tone = self._suggest_tone(sender, subject, body, is_servicenow)
            
            return {
                "needs_response": needs_response,
                "response_type": response_type,
                "urgency": urgency,
                "key_points": key_points,
                "suggested_tone": suggested_tone,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Email analysis failed: {str(e)}"}
    
    def _needs_response(self, subject: str, sender: str, body: str, is_servicenow: bool) -> bool:
        """Determine if email needs a response"""
        
        # Automatic no-response indicators
        no_response_indicators = [
            "no-reply", "noreply", "do-not-reply", "newsletter", "automated",
            "marketing", "promotion", "unsubscribe", "notification only",
            "for your information", "fyi"
        ]
        
        # Response required indicators
        response_indicators = [
            "please", "request", "need", "help", "question", "?",
            "meeting", "schedule", "urgent", "asap", "respond",
            "reply", "feedback", "approval", "confirm"
        ]
        
        text_to_check = f"{subject} {sender} {body}".lower()
        
        # Check for no-response indicators first
        if any(indicator in text_to_check for indicator in no_response_indicators):
            return False
        
        # ServiceNow emails usually need responses
        if is_servicenow:
            return True
        
        # Check for response indicators
        if any(indicator in text_to_check for indicator in response_indicators):
            return True
        
        # Default to needing response for personal/business emails
        return True
    
    def _determine_response_type(self, subject: str, body: str, is_servicenow: bool) -> str:
        """Determine what type of response is needed"""
        
        text_to_check = f"{subject} {body}".lower()
        
        if is_servicenow:
            if "incident" in text_to_check or "inc" in text_to_check:
                return "servicenow_incident_response"
            elif "request" in text_to_check or "req" in text_to_check:
                return "servicenow_request_response"
            else:
                return "servicenow_general_response"
        
        if "meeting" in text_to_check or "schedule" in text_to_check:
            return "meeting_response"
        elif "question" in text_to_check or "?" in text_to_check:
            return "question_answer"
        elif "approval" in text_to_check or "approve" in text_to_check:
            return "approval_response"
        elif "thank" in text_to_check:
            return "acknowledgment"
        else:
            return "general_response"
    
    def _determine_urgency(self, subject: str, body: str, priority: str, is_servicenow: bool) -> str:
        """Determine response urgency"""
        
        if priority == "high":
            return "high"
        
        text_to_check = f"{subject} {body}".lower()
        
        high_urgency_indicators = [
            "urgent", "asap", "immediate", "emergency", "critical",
            "deadline", "today", "now"
        ]
        
        if any(indicator in text_to_check for indicator in high_urgency_indicators):
            return "high"
        elif is_servicenow:
            return "medium"
        else:
            return "low"
    
    def _extract_key_points(self, subject: str, body: str) -> List[str]:
        """Extract key points from email"""
        key_points = []
        
        # Add subject as key point if meaningful
        if subject and len(subject.strip()) > 5:
            key_points.append(f"Subject: {subject}")
        
        # Extract sentences that might be key points
        sentences = body.split('.')
        for sentence in sentences[:3]:  # Take first 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                key_points.append(sentence)
        
        return key_points[:5]  # Limit to 5 key points
    
    def _suggest_tone(self, sender: str, subject: str, body: str, is_servicenow: bool) -> str:
        """Suggest appropriate tone for response"""
        
        text_to_check = f"{subject} {body}".lower()
        
        if is_servicenow:
            return "professional_technical"
        elif "thank" in text_to_check:
            return "appreciative"
        elif any(word in text_to_check for word in ["urgent", "problem", "issue", "error"]):
            return "professional_helpful"
        elif "meeting" in text_to_check:
            return "professional_collaborative"
        else:
            return "professional_friendly"

class ResponseGeneratorTool(BaseTool):
    """Tool for generating email responses"""
    
    name: str = "Response Generator Tool"
    description: str = "Generates appropriate email responses based on analysis"
    
    def _run(self, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate email response based on email content and analysis
        
        Args:
            email_data: Original email data
            analysis: Email analysis results
            
        Returns:
            Generated response data
        """
        try:
            if not analysis.get("needs_response", False):
                return {
                    "response_needed": False,
                    "message": "No response required for this email"
                }
            
            response_type = analysis.get("response_type", "general_response")
            suggested_tone = analysis.get("suggested_tone", "professional_friendly")
            key_points = analysis.get("key_points", [])
            
            # Generate response based on type
            response_content = self._generate_response_content(
                email_data, response_type, suggested_tone, key_points
            )
            
            return {
                "response_needed": True,
                "response_type": response_type,
                "suggested_tone": suggested_tone,
                "response_content": response_content,
                "generation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Response generation failed: {str(e)}"}
    
    def _generate_response_content(self, email_data: Dict[str, Any], 
                                 response_type: str, tone: str, 
                                 key_points: List[str]) -> str:
        """Generate the actual response content"""
        
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")
        
        # Extract sender name (simple extraction)
        sender_name = self._extract_sender_name(sender)
        
        # Generate greeting
        greeting = f"Hi{' ' + sender_name if sender_name else ''},"
        
        # Generate main response based on type
        main_content = self._get_response_template(response_type, email_data)
        
        # Generate closing
        closing = self._get_closing(tone)
        
        response = f"""{greeting}

{main_content}

{closing}

Best regards,
[Your Name]"""
        
        return response
    
    def _extract_sender_name(self, sender: str) -> str:
        """Extract sender name from email address"""
        try:
            if "<" in sender:
                name_part = sender.split("<")[0].strip()
                if name_part and not "@" in name_part:
                    return name_part.strip('"').split()[0]
            return ""
        except:
            return ""
    
    def _get_response_template(self, response_type: str, email_data: Dict[str, Any]) -> str:
        """Get response template based on type"""
        
        templates = {
            "servicenow_incident_response": """Thank you for the ServiceNow incident notification. I acknowledge receipt of this incident and will investigate accordingly.

I will provide updates as the investigation progresses and work towards resolution within the specified SLA timeframe.""",
            
            "servicenow_request_response": """Thank you for your ServiceNow request. I have received your request and will process it according to our standard procedures.

I will keep you updated on the progress and notify you once the request has been completed.""",
            
            "meeting_response": """Thank you for the meeting invitation. I will review my calendar and get back to you with my availability.

Please let me know if there are any specific agenda items or materials I should prepare for the meeting.""",
            
            "question_answer": """Thank you for your question. I will review the details and provide you with a comprehensive response.

If you need any immediate clarification or have additional questions, please don't hesitate to reach out.""",
            
            "approval_response": """Thank you for submitting this for approval. I will review the details and provide my response within the required timeframe.

If I need any additional information or clarification, I will reach out to you directly.""",
            
            "acknowledgment": """Thank you for your email. I appreciate you taking the time to reach out and provide this information.

I have noted the details and will take any necessary actions as appropriate.""",
            
            "general_response": """Thank you for your email. I have received your message and will respond appropriately.

If this matter is urgent or you need immediate assistance, please feel free to contact me directly."""
        }
        
        return templates.get(response_type, templates["general_response"])
    
    def _get_closing(self, tone: str) -> str:
        """Get appropriate closing based on tone"""
        
        closings = {
            "professional_technical": "If you have any technical questions or need further assistance, please don't hesitate to contact me.",
            "appreciative": "Thank you again for your communication. I truly appreciate it.",
            "professional_helpful": "I'm here to help resolve this matter promptly. Please let me know if you need anything else.",
            "professional_collaborative": "I look forward to our collaboration on this matter.",
            "professional_friendly": "Thank you for reaching out. I look forward to hearing from you."
        }
        
        return closings.get(tone, closings["professional_friendly"])

class EmailSaverTool(BaseTool):
    """Tool for saving email analysis and responses to files"""
    
    name: str = "Email Saver Tool"
    description: str = "Saves email analysis results and generated responses to output files"
    
    def _run(self, email_data: Dict[str, Any], analysis: Dict[str, Any], 
             response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save email processing results to files"""
        
        try:
            # Create output directory
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete analysis
            analysis_file = os.path.join(output_dir, f"email_analysis_{timestamp}.json")
            analysis_data = {
                "email_data": email_data,
                "analysis": analysis,
                "response_data": response_data,
                "processed_at": datetime.now().isoformat()
            }
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            # Save response text if generated
            if response_data.get("response_needed", False):
                response_file = os.path.join(output_dir, f"email_response_{timestamp}.txt")
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(f"Subject: Re: {email_data.get('subject', '')}\n")
                    f.write(f"In response to: {email_data.get('sender', '')}\n")
                    f.write(f"Generated at: {datetime.now().isoformat()}\n")
                    f.write("-" * 50 + "\n\n")
                    f.write(response_data.get("response_content", ""))
            
            return {
                "success": True,
                "analysis_file": analysis_file,
                "response_file": response_file if response_data.get("response_needed") else None,
                "message": "Email processing results saved successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to save results: {str(e)}"}
