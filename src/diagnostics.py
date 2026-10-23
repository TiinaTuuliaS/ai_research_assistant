"""Bounded, persistent error diagnostics without prompts or provider bodies."""
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import traceback

from pydantic import ValidationError


def error_details(exc):
    chain, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        detail = {
            "type": type(exc).__name__,
            "frames": [f"{Path(frame.filename).name}:{frame.name}:{frame.lineno}"
                       for frame in traceback.extract_tb(exc.__traceback__)],
        }
        if isinstance(exc, ValidationError):
            detail["validation"] = [{"type": error["type"], "loc": error["loc"]}
                for error in exc.errors(include_input=False, include_context=False, include_url=False)]
        status = getattr(exc, "status_code", None)
        if isinstance(status, int):
            detail["status_code"] = status
        # Only machine identifiers, never arbitrary exception messages/bodies.
        for field in ("code", "param"):
            value = getattr(exc, field, None)
            if isinstance(value, str) and len(value) <= 80 and all(
                c.isalnum() or c in "_.[]" for c in value
            ):
                detail[field] = value
        chain.append(detail)
        exc = exc.__cause__ or (None if exc.__suppress_context__ else exc.__context__)
    return chain


def configure_diagnostics(path=None):
    logger = logging.getLogger("research.diagnostics")
    if not logger.handlers:
        target = Path(path or os.getenv("DIAGNOSTICS_PATH") or Path(__file__).resolve().parent.parent / ".runtime" / "backend-errors.log")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(target, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            logger.addHandler(handler)
        except OSError:
            logging.getLogger(__name__).warning("Persistent diagnostics unavailable; using console logging")
    logger.setLevel(logging.ERROR)
    return logger


def record_failure(exc, *, operation, job_id=None):
    configure_diagnostics().error(json.dumps({"operation": operation, "job_id": job_id,
                                            "exceptions": error_details(exc)}, ensure_ascii=False))
