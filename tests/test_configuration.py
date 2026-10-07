from pathlib import Path
import unittest
import yaml
from src.ai_research_assistant.quality import QUALITY_RULES


class ConfigurationTests(unittest.TestCase):
    def test_task_configuration_is_utf8_and_preserves_required_headings(self):
        config_dir = Path(__file__).resolve().parents[1] / "src/ai_research_assistant/config"
        tasks = yaml.safe_load((config_dir / "tasks.yaml").read_text(encoding="utf-8"))
        yaml.safe_load((config_dir / "agents.yaml").read_text(encoding="utf-8"))
        description = tasks["report_task"]["description"]
        self.assertIn("## Näytön vahvuus ja puutteet", description)
        self.assertIn("## Lähteet", description)
        contracts = yaml.safe_load((config_dir / "deliverables.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(contracts), {"demand", "competition", "market"})
        for mode, outputs in contracts.items():
            self.assertEqual(set(outputs), set(tasks))
            self.assertEqual(len(set(outputs.values())), 5)
            inputs = dict(topic="Test", current_year="2026", goal="Question", research_type=mode,
                          target_market="Finland", budget="Unknown", language="suomi", quality_rules=QUALITY_RULES)
            inputs.update({f"{name}_deliverable": value for name, value in outputs.items()})
            for name, task in tasks.items():
                self.assertIn(outputs[name], task["description"].format(**inputs))
                self.assertIn(outputs[name], task["expected_output"].format(**inputs))

    def test_actual_crew_prepares_each_mode_without_running_models(self):
        import os
        from unittest.mock import patch
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-not-used", "SERPER_API_KEY": "test-not-used"}):
            for mode in ("demand", "competition", "market"):
                assistant = AiResearchAssistant()
                crew = assistant.crew()
                inputs = assistant.prepare({"research_type": mode, "topic": "Test", "language": "suomi", "current_year": "2026"})
                self.assertEqual(len(crew.tasks), 5)
                for task in crew.tasks:
                    self.assertIn(inputs[f"{task.name}_deliverable"], task.description.format(**inputs))
                    self.assertIn(inputs[f"{task.name}_deliverable"], task.expected_output.format(**inputs))
                    if task.name == "research_task":
                        from src.ai_research_assistant.research_result import ResearchResult
                        self.assertIs(task.output_pydantic, ResearchResult)
                        self.assertIsNotNone(task.callback)
                    else:
                        self.assertIsNotNone(task.guardrail)
            self.assertEqual(assistant.prepare({})["research_type"], "market")
            with self.assertRaises(ValueError):
                assistant.prepare({"research_type": "invalid"})
