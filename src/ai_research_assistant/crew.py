from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from crewai.tasks.task_output import TaskOutput
from dotenv import load_dotenv

from .citations import validate_citations
from .tools.search_tool import SourceSearchTool


@CrewBase
class AiResearchAssistant:
    """Sequential market research with per-run source provenance."""

    agents: list[BaseAgent]
    tasks: list[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        load_dotenv()
        self.llm = LLM(model="openai/gpt-4o-mini")
        self.search_tool = SourceSearchTool()

    @before_kickoff
    def prepare(self, inputs):
        self.search_tool.sources.clear()
        return inputs

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            tools=[self.search_tool], llm=self.llm, cache=False, verbose=False,
        )

    @agent
    def trend_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["trend_analyst"],  # type: ignore[index]
            tools=[self.search_tool], llm=self.llm, cache=False, verbose=False,
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],  # type: ignore[index]
            llm=self.llm, verbose=False,
        )

    @agent
    def strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["strategist"],  # type: ignore[index]
            llm=self.llm, verbose=False,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],  # type: ignore[index]
            llm=self.llm, verbose=False,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
            agent=self.researcher(),
        )

    @task
    def trend_task(self) -> Task:
        return Task(
            config=self.tasks_config["trend_task"],  # type: ignore[index]
            agent=self.trend_analyst(), context=[self.research_task()],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],  # type: ignore[index]
            agent=self.analyst(), context=[self.research_task(), self.trend_task()],
        )

    @task
    def strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["strategy_task"],  # type: ignore[index]
            agent=self.strategist(), context=[self.research_task(), self.trend_task(), self.analysis_task()],
        )

    def check_sources(self, output: TaskOutput) -> tuple[bool, Any]:
        return validate_citations(output.raw, self.search_tool.sources)

    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_task"],  # type: ignore[index]
            agent=self.writer(),
            context=[self.research_task(), self.trend_task(), self.analysis_task(), self.strategy_task()],
            guardrail=self.check_sources, guardrail_max_retries=2,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential,
                    cache=False, verbose=False)
