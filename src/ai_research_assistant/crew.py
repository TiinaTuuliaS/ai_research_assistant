from typing import Any
import os
from pathlib import Path
import yaml

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from crewai.tasks.task_output import TaskOutput
from dotenv import load_dotenv

from .citations import validate_citations
from .quality import QUALITY_RULES, review_output
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
        model = os.getenv("RESEARCH_MODEL", "openai/gpt-4.1-mini")
        self.llm = LLM(model=model, temperature=0.2)
        self.reviewer = LLM(model=model, temperature=0, max_tokens=4000)
        self.brief = {}
        self.accepted_outputs = []
        self.search_tool = SourceSearchTool()

    @before_kickoff
    def prepare(self, inputs):
        self.search_tool.reset_run()
        self.accepted_outputs.clear()
        inputs = dict(inputs or {})
        inputs["goal"] = inputs.get("goal") or "Explore opportunities; explicitly label this assumed goal"
        inputs["target_market"] = inputs.get("target_market") or "Not specified; state any market assumptions explicitly"
        inputs["budget"] = inputs.get("budget") or "Not specified; do not assume a budget"
        mode = inputs.get("research_type") or "market"
        contracts = yaml.safe_load((Path(__file__).parent / "config/deliverables.yaml").read_text(encoding="utf-8"))
        if mode not in contracts:
            raise ValueError("Unknown research type")
        inputs["research_type"] = mode
        self.brief = {key: inputs.get(key, "") for key in
                      ("topic", "language", "goal", "target_market", "budget", "research_type")}
        inputs["quality_rules"] = QUALITY_RULES
        for name, contract in contracts[mode].items():
            inputs[f"{name}_deliverable"] = contract
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
            guardrail=self.check_quality, guardrail_max_retries=1,
        )

    @task
    def trend_task(self) -> Task:
        return Task(
            config=self.tasks_config["trend_task"],  # type: ignore[index]
            agent=self.trend_analyst(), context=[self.research_task()],
            guardrail=self.check_quality, guardrail_max_retries=1,
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],  # type: ignore[index]
            agent=self.analyst(), context=[self.research_task(), self.trend_task()],
            guardrail=self.check_quality, guardrail_max_retries=1,
        )

    @task
    def strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["strategy_task"],  # type: ignore[index]
            agent=self.strategist(), context=[self.research_task(), self.trend_task(), self.analysis_task()],
            guardrail=self.check_quality, guardrail_max_retries=1,
        )

    def check_quality(self, output: TaskOutput) -> tuple[bool, Any]:
        valid, result = review_output(output.raw, sources=self.search_tool.sources,
                                      brief=self.brief, previous=self.accepted_outputs,
                                      reviewer=self.reviewer)
        if valid:
            self.accepted_outputs.append({"agent": output.agent, "text": result})
        return valid, result

    def check_sources(self, output: TaskOutput) -> tuple[bool, Any]:
        valid, result = review_output(output.raw, sources=self.search_tool.sources,
                                      brief=self.brief, previous=self.accepted_outputs,
                                      reviewer=self.reviewer)
        if not valid:
            return valid, result
        return validate_citations(result, self.search_tool.sources, require_evidence_notes=True)

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
