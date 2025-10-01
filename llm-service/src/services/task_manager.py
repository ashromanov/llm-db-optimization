"""
Service to manage tasks and their statuss.
"""

import asyncio
import uuid
from enum import Enum


class Status(Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DONE = "DONE"


class TrackedTask:
    def __init__(self, task: asyncio.Task):
        self.id = str(uuid.uuid4())
        self._task = task
        self.status = Status.RUNNING
        self.result: dict = None


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, TrackedTask] = {}

    def add_task(self, task: asyncio.Task) -> str:
        """
        Add and track a task.
        """
        tracked = TrackedTask(task)
        self._tasks[tracked.id] = tracked
        return tracked.id

    def get_status(self, taskid: str) -> Status:
        tracked = self._tasks[taskid]
        if tracked._task.done():
            tracked.status = Status.DONE
            tracked.result = tracked._task.result()
        return tracked.status

    def get_result(self, taskid: str):
        return self._tasks[taskid].result


task_manager = TaskManager()
