#!/usr/bin/env python
import sys
import warnings
from dotenv import load_dotenv

# Add this line to suppress the warning
warnings.filterwarnings("ignore", message=".*not a Python type.*")
# Keep your existing warning filter
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from gmail_crew_ai.crew import GmailCrewAi

def run():
    """Run the Gmail Crew AI."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get user input for number of emails to process
        try:
            email_limit = input("How many emails would you like to process? (default: 5): ")
            if email_limit.strip() == "":
                email_limit = 5
            else:
                email_limit = int(email_limit)
                if email_limit <= 0:
                    print("Number must be positive. Using default of 5.")
                    email_limit = 5
        except ValueError:
            print("Invalid input. Using default of 5 emails.")
            email_limit = 5
        
        print(f"Processing {email_limit} emails...")
        
        # Create and run the crew with the specified email limit
        result = GmailCrewAi().crew().kickoff(inputs={'email_limit': email_limit})
        
        # Check if result is empty or None
        if not result:
            print("\nNo emails were processed. Inbox might be empty.")
            return 0
            
        # Print the result in a clean way
        if result:
            print("\nCrew execution completed successfully! 🎉")
            print("Results have been saved to the output directory.")
            return 0  # Return success code
        else:
            print("\nCrew execution completed but no results were returned.")
            return 0  # Still consider this a success
    except ImportError as e:
        if "servicenow_email_analyst" in str(e) or "agents" in str(e):
            print("\n❌ Configuration Error:")
            print("Missing agent configuration. Please ensure all agents are defined in:")
            print("  src/gmail_crew_ai/config/agents.yaml")
            print("\nRequired agents:")
            print("  - response_generator")
            print("  - servicenow_email_analyst") 
            print("  - response_strategist")
            print("  - content_generator")
            print("  - quality_reviewer")
            print("  - workflow_coordinator")
            return 1
        else:
            print(f"\n❌ Import Error: {e}")
            return 1
    except FileNotFoundError as e:
        print(f"\n❌ File Not Found: {e}")
        print("Please ensure all configuration files exist in src/gmail_crew_ai/config/")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("Please check your configuration and try again.")
        return 1

def train():
    """Train the crew for 'n' iterations."""
    try:
        load_dotenv()
        n_iterations = int(input("Enter the number of training iterations: "))
        GmailCrewAi().crew().train(n_iterations=n_iterations)
        print(f"\nTraining completed for {n_iterations} iterations! 🎓")
        return 0
    except Exception as e:
        print(f"\n❌ Training Error: {e}")
        return 1

def replay():
    """Replay the crew execution from a specific task."""
    try:
        load_dotenv()
        task_id = input("Enter the task ID to replay from: ")
        GmailCrewAi().crew().replay(task_id=task_id)
        print(f"\nReplay completed from task {task_id}! 🔄")
        return 0
    except Exception as e:
        print(f"\n❌ Replay Error: {e}")
        return 1

def test():
    """Test the crew setup and configuration."""
    try:
        load_dotenv()
        print("🧪 Testing crew configuration...")
        crew = GmailCrewAi().crew()
        print("✅ Crew initialized successfully!")
        print(f"📊 Agents: {len(crew.agents)}")
        print(f"📋 Tasks: {len(crew.tasks)}")
        print("🎯 Configuration test passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run())  # Use the return value as the exit code
