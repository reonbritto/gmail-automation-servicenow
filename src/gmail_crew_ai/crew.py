from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from crewai_tools import FileReadTool
import json
import os
from typing import List, Dict, Any, Callable
from pydantic import SkipValidation
from datetime import date, datetime

from gmail_crew_ai.tools.gmail_tools import GetUnreadEmailsTool, SaveDraftTool
from gmail_crew_ai.models import EmailResponse, EmailDetails, EmailResponseList

@CrewBase
class GmailCrewAi():
	"""ServiceNow Ticket Response Automation Crew"""
	
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@before_kickoff
	def fetch_emails(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
		"""Fetch emails before starting the crew and calculate ages."""
		print("Fetching emails before starting the crew...")
		
		# Get the email limit from inputs
		email_limit = inputs.get('email_limit', 5)
		print(f"Fetching {email_limit} emails...")
		
		# Create the output directory if it doesn't exist
		os.makedirs("output", exist_ok=True)
		
		# Use the GetUnreadEmailsTool directly
		try:
			email_tool = GetUnreadEmailsTool()
			email_tuples = email_tool._run(limit=email_limit)
			
			if not email_tuples:
				print("No unread emails found or error occurred during fetching.")
				# Create an empty file to indicate the process ran but found no emails
				with open('output/fetched_emails.json', 'w') as f:
					json.dump([], f)
				return inputs
			
			# Convert email tuples to EmailDetails objects with pre-calculated ages
			emails = []
			today = date.today()
			
			for email_tuple in email_tuples:
				try:
					email_detail = EmailDetails.from_email_tuple(email_tuple)
					
					# Calculate age if date is available
					if email_detail.date:
						try:
							email_date_obj = datetime.strptime(email_detail.date, "%Y-%m-%d").date()
							email_detail.age_days = (today - email_date_obj).days
							print(f"Email date: {email_detail.date}, age: {email_detail.age_days} days")
						except Exception as e:
							print(f"Error calculating age for email date {email_detail.date}: {e}")
							email_detail.age_days = None
					
					emails.append(email_detail.dict())
				except Exception as e:
					print(f"Error processing email: {e}")
					continue
			
			# Save emails to file
			with open('output/fetched_emails.json', 'w') as f:
				json.dump(emails, f, indent=2)
			
			print(f"Fetched and saved {len(emails)} emails to output/fetched_emails.json")
			
		except Exception as e:
			print(f"Error in fetch_emails: {e}")
			import traceback
			traceback.print_exc()
			# Create an empty file to indicate the process ran but encountered an error
			with open('output/fetched_emails.json', 'w') as f:
				json.dump([], f)
		
		return inputs
	
	llm = LLM(
		model=os.getenv("MODEL"),
		api_key=os.getenv("GEMINI_API_KEY"),
	)

	@agent
	def response_generator(self) -> Agent:
		"""The email response generator agent."""
		return Agent(
			config=self.agents_config['response_generator'],
			tools=[SaveDraftTool(), FileReadTool()],
			llm=self.llm,
		)
	
	@task
	def servicenow_ticket_response_task(self) -> Task:
		"""ServiceNow Ticket Processing Task"""
		return Task(
			config=self.tasks_config['servicenow_ticket_response_task'],
			agent=self.response_generator()
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the email processing crew."""
		# Use self.agents and self.tasks which are populated by the decorators
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
		)
