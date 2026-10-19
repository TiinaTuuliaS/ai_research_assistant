"""Per-run task events; no timers or synthetic agent responses."""
from contextlib import contextmanager

from crewai.events import TaskStartedEvent, crewai_event_bus


@contextmanager
def track_tasks(crew, notify, display_output=None):
    task_indexes = {task.id: index for index, task in enumerate(crew.tasks)}

    def started(source, event):
        index = task_indexes.get(source.id)
        if index is not None:
            notify(index, "running", None)

    previous = [task.callback for task in crew.tasks]
    for index, task in enumerate(crew.tasks):
        def completed(output, index=index, original=task.callback):
            if original:
                original(output)
            text = display_output(index, output) if display_output else output.raw
            notify(index, "completed", text)
        task.callback = completed
    crewai_event_bus.on(TaskStartedEvent)(started)
    try:
        yield
    finally:
        crewai_event_bus.off(TaskStartedEvent, started)
        for task, callback in zip(crew.tasks, previous):
            task.callback = callback
