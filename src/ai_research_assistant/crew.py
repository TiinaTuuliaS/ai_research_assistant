from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.search_tool import search_tool
import os

llm = LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

@CrewBase
class AiResearchAssistant():
    """AiResearchAssistant crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # 🔥 AGENTS
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[search_tool],
            llm=llm,
            verbose=True
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            llm=llm,
            verbose=True
        )

    @agent
    def strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['strategist'],
            llm=llm,
            verbose=True
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            llm=llm,
            verbose=True
        )

    # 🔥 TASKS

    @task
    def research_task(self) -> Task:
        return Task(
        config=self.tasks_config['research_task'],
        agent=self.researcher()
    )

    @task
    def analysis_task(self) -> Task:
        return Task(
        config=self.tasks_config['analysis_task'],
        agent=self.analyst()
    )

    @task
    def strategy_task(self) -> Task:
        return Task(
        config=self.tasks_config['strategy_task'],
        agent=self.strategist()
    )

    @task
    def report_task(self) -> Task:
        return Task(
        config=self.tasks_config['report_task'],
        agent=self.writer()
    )

    # 🔥 CREW
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )