#!/usr/bin/env python
import sys
import warnings
import json
from pathlib import Path
from crewai import Crew, Agent, Task
import yaml
import os
from dotenv import load_dotenv
from gmail_crew_ai.tools.gmail_tools import fetch_unread_emails, save_email_draft

# Add this line to suppress the warning
warnings.filterwarnings("ignore", message=".*not a Python type.*")
# Keep your existing warning filter
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Load environment variables
load_dotenv()

# Ensure output directory exists
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

def load_config(config_type):
    """Load configuration from YAML files."""
    config_path = Path(__file__).parent / "config" / f"{config_type}.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def create_agents():
    """Create agents based on configuration."""
    agents_config = load_config("agents")
    agents = {}
    
    for agent_id, agent_data in agents_config.items():
        agents[agent_id] = Agent(
            role=agent_data.get("role"),
            goal=agent_data.get("goal"),
            backstory=agent_data.get("backstory"),
            verbose=agent_data.get("verbose", True),
            allow_delegation=agent_data.get("allow_delegation", False),
            memory=agent_data.get("memory", False)
        )
    
    return agents

def create_tasks(agents):
    """Create tasks based on configuration."""
    tasks_config = load_config("tasks")
    tasks = []
    
    for task_id, task_data in tasks_config.items():
        agent_id = task_data.get("agent")
        if agent_id not in agents:
            raise ValueError(f"Agent '{agent_id}' not found for task '{task_id}'")
        
        tasks.append(Task(
            description=task_data.get("description"),
            expected_output=task_data.get("expected_output"),
            agent=agents[agent_id],
            output_file=task_data.get("output_file")
        ))
    
    return tasks

def before_kickoff():
    """Tasks to run before starting the crew."""
    # Fetch unread emails and save to file
    emails = fetch_unread_emails(max_emails=20)
    with open(output_dir / "fetched_emails.json", "w") as f:
        json.dump(emails, f, indent=2)
    
    print(f"Fetched {len(emails)} unread emails")

def run():
    """Main function to run the crew."""
    print("Starting Gmail & ServiceNow automation...")
    
    # Run pre-tasks
    before_kickoff()
    
    # Create agents and tasks
    agents = create_agents()
    tasks = create_tasks(agents)
    
    # Create and run the crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=2
    )
    
    # Execute the crew's tasks
    results = crew.kickoff()
    
    print("Automation completed successfully!")
    return results

def train():
    """Function to train the system with user preferences."""
    print("Training system with user preferences...")
    # Implementation for training would go here
    pass

def replay():
    """Function to replay previous runs."""
    print("Replaying previous runs...")
    # Implementation for replaying would go here
    pass

def test():
    """Function to run tests."""
    print("Running tests...")
    # Implementation for tests would go here
    pass

if __name__ == "__main__":
    sys.exit(run())  # Use the return value as the exit code
