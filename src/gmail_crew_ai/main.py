#!/usr/bin/env python
import sys
import os
from typing import List, Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from gmail_crew_ai.tools.gmail_reader import read_gmail_emails
from gmail_crew_ai.tools.email_tools import analyze_email_content, generate_email_response, save_email_results

def run():
    """
    Run the Gmail email processing workflow.
    """
    try:
        print("🔄 Starting Gmail Email Processing...")
        print("=" * 60)
        
        # Get number of emails to process
        try:
            limit = int(input("How many emails would you like to process? (default: 5): ") or "5")
            if limit <= 0:
                limit = 5
        except ValueError:
            limit = 5
            print(f"Invalid input. Using default limit of {limit} emails.")
        
        print(f"\n📧 Processing up to {limit} unread emails from Gmail...")
        
        # Step 1: Read emails from Gmail
        print("\n1. 📥 Reading emails from Gmail...")
        result = read_gmail_emails(limit=limit)
        
        if "error" in result:
            print(f"❌ Error reading emails: {result['error']}")
            return
        
        emails = result.get("emails", [])
        
        if not emails:
            print("ℹ️  No emails found to process.")
            return
        
        print(f"✅ Successfully read {len(emails)} emails")
        
        # Process each email
        processed_emails = []
        responses_generated = 0
        
        for i, email_data in enumerate(emails, 1):
            print(f"\n2.{i} 🔍 Processing email: {email_data.get('subject', 'No Subject')[:50]}...")
            print(f"     From: {email_data.get('sender', 'Unknown')}")
            print(f"     Priority: {email_data.get('priority', 'normal').upper()}")
            
            # Step 2: Analyze email
            print(f"     📊 Analyzing email content...")
            analysis = analyze_email_content(email_data)
            
            if "error" in analysis:
                print(f"     ❌ Analysis error: {analysis['error']}")
                continue
            
            print(f"     📋 Needs response: {analysis.get('needs_response', False)}")
            print(f"     🎯 Response type: {analysis.get('response_type', 'N/A')}")
            print(f"     ⚡ Urgency: {analysis.get('urgency', 'N/A')}")
            
            # Step 3: Generate response if needed
            response_data = {"response_needed": False}
            if analysis.get("needs_response", False):
                print(f"     ✍️  Generating response...")
                response_data = generate_email_response(email_data, analysis)
                
                if "error" in response_data:
                    print(f"     ❌ Response generation error: {response_data['error']}")
                else:
                    responses_generated += 1
                    print(f"     ✅ Response generated successfully")
            else:
                print(f"     ⏭️  No response needed")
            
            # Step 4: Save results
            print(f"     💾 Saving results...")
            save_result = save_email_results(email_data, analysis, response_data)
            
            if "error" in save_result:
                print(f"     ❌ Save error: {save_result['error']}")
            else:
                print(f"     ✅ Results saved")
            
            processed_emails.append({
                "email": email_data,
                "analysis": analysis,
                "response": response_data,
                "save_result": save_result
            })
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 PROCESSING SUMMARY")
        print("=" * 60)
        print(f"📧 Total emails processed: {len(processed_emails)}")
        print(f"✍️  Responses generated: {responses_generated}")
        print(f"📁 Results saved to: ./output/ directory")
        
        # Show response preview
        if responses_generated > 0:
            print(f"\n📝 RESPONSE PREVIEW")
            print("-" * 40)
            for result in processed_emails:
                if result["response"].get("response_needed", False):
                    email_subject = result["email"].get("subject", "No Subject")
                    response_content = result["response"].get("response_content", "")
                    
                    print(f"\n📧 Re: {email_subject}")
                    print("📄 Response preview:")
                    # Show first 200 characters of response
                    preview = response_content[:200] + "..." if len(response_content) > 200 else response_content
                    print(f"   {preview}")
        
        print(f"\n🎉 Email processing completed successfully!")
        print(f"💡 Check the ./output/ directory for detailed results and generated responses.")
        print(f"⚠️  Please review all generated responses before sending!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("🔧 Please check your configuration and try again.")

def train():
    """
    Train functionality (placeholder for future crew training)
    """
    print("Training functionality not implemented in this version.")

def replay():
    """
    Replay functionality (placeholder for future crew replay)
    """
    print("Replay functionality not implemented in this version.")

def test():
    """
    Test the email processing with a limited set
    """
    print("🧪 Running test mode...")
    # Process only 2 emails for testing
    run()

if __name__ == "__main__":
    run()
