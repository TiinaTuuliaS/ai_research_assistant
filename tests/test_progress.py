import unittest
from types import SimpleNamespace

from crewai import Task
from crewai.events import TaskStartedEvent, crewai_event_bus
from crewai.tasks.task_output import TaskOutput
from src.ai_research_assistant.progress import track_tasks


class ProgressTests(unittest.TestCase):
    def test_real_events_are_scoped_and_callbacks_cleaned_up(self):
        task = Task(description="Research", expected_output="Findings")
        other = Task(description="Other research", expected_output="Other findings")
        crew = SimpleNamespace(tasks=[task])
        received = []
        def emit(source):
            future = crewai_event_bus.emit(source, TaskStartedEvent(task=source, context=""))
            if future:
                future.result(timeout=5)
        with track_tasks(crew, lambda *event: received.append(event)):
            emit(other)
            self.assertEqual(received, [])
            emit(task)
            self.assertEqual(received, [(0, "running", None)])
            task.callback(TaskOutput(description="Research", raw="Actual output", agent="Researcher"))
            self.assertEqual(received[-1], (0, "completed", "Actual output"))
        self.assertIsNone(task.callback)
        emit(task)
        self.assertEqual(len(received), 2)

    def test_cleanup_after_failure(self):
        task = Task(description="Research", expected_output="Findings")
        with self.assertRaises(ValueError):
            with track_tasks(SimpleNamespace(tasks=[task]), lambda *args: None):
                raise ValueError("failed")
        self.assertIsNone(task.callback)
