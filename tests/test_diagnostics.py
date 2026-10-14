import logging
from pathlib import Path
import tempfile
import unittest

from pydantic import BaseModel, ValidationError

from src.diagnostics import configure_diagnostics, error_details


class DiagnosticTests(unittest.TestCase):
    def test_validation_cause_survives_without_input_or_exception_message(self):
        class Value(BaseModel):
            count: int
        try:
            try:
                Value(count="private-input-secret")
            except ValidationError as cause:
                raise RuntimeError("private-provider-body") from cause
        except RuntimeError as exc:
            details = error_details(exc)
        self.assertEqual([d["type"] for d in details], ["RuntimeError", "ValidationError"])
        self.assertEqual(details[1]["validation"], [{"type": "int_parsing", "loc": ("count",)}])
        self.assertNotIn("private", str(details))

    def test_log_is_persistent_and_configuration_does_not_duplicate_handlers(self):
        logger = logging.getLogger("research.diagnostics")
        original = logger.handlers[:]
        logger.handlers = []
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "errors.log"
                configure_diagnostics(path).error("test diagnostic")
                configure_diagnostics(path)
                self.assertEqual(len(logger.handlers), 1)
                self.assertIn("test diagnostic", path.read_text(encoding="utf-8"))
                for handler in logger.handlers:
                    handler.close()
                logger.handlers = []
        finally:
            logger.handlers = original
