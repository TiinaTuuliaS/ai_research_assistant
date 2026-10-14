"""Compatibility for structured research retries in CrewAI 1.10.1."""
from crewai import Agent
from pydantic import BaseModel


class ResearchAgent(Agent):
    def execute_task(self, task, context=None, tools=None):
        result = super().execute_task(task=task, context=context, tools=tools)
        # Task._execute_core handles BaseModel on the first execution, but
        # _invoke_guardrail_function assigns retry results directly to raw:str.
        # Let CrewAI's normal exporter validate the serialized retry result.
        if task.retry_count and isinstance(result, BaseModel):
            return result.model_dump_json()
        return result
