#!/usr/bin/env python
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@CrewBase
class GmailCrewAi():
    """Gmail Crew AI class"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def response_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['response_generator'],
            verbose=True
        )

    @agent
    def servicenow_email_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['servicenow_email_analyst'],
            verbose=True
        )

    @agent
    def response_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['response_strategist'],
            verbose=True
        )

    @agent
    def content_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['content_generator'],
            verbose=True
        )

    @agent
    def quality_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['quality_reviewer'],
            verbose=True
        )

    @agent
    def workflow_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['workflow_coordinator'],
            verbose=True
        )

    @task
    def response_task(self) -> Task:
        return Task(
            config=self.tasks_config['response_task'],
            agent=self.response_generator()
        )

    @task
    def analyze_servicenow_email(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_servicenow_email'],
            agent=self.servicenow_email_analyst()
        )

    @task
    def determine_response_strategy(self) -> Task:
        return Task(
            config=self.tasks_config['determine_response_strategy'],
            agent=self.response_strategist()
        )

    @task
    def generate_email_response(self) -> Task:
        return Task(
            config=self.tasks_config['generate_email_response'],
            agent=self.content_generator()
        )

    @task
    def review_response_quality(self) -> Task:
        return Task(
            config=self.tasks_config['review_response_quality'],
            agent=self.quality_reviewer()
        )

    @task
    def coordinate_email_workflow(self) -> Task:
        return Task(
            config=self.tasks_config['coordinate_email_workflow'],
            agent=self.workflow_coordinator()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Gmail Crew AI crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
