"""
Service to manage tasks and their states.
"""

import uuid
from enum import Enum


class State(Enum):
    RUNNING: str = "RUNNING"
    FAILED: str = "FAILED"
    DONE: str = "DONE"


class TaskManager:
    def __init__(self):
        self._tasks = dict[str, str]

    def create_task(self) -> str:
        """
        Create task.

        Return:
            str: ID of the created task.
        """
        id = str(uuid.uuid4())
        self._tasks[id] = State.RUNNING
        return id

    # Здесь логику можно по разному рассмотреть
    def get_task_state(self, task_id: str) -> str:
        """
        Gets state of the task by ID.

        Args:
            task_id (str): ID of the target task.

        Returns:
            str: state ('RUNNING', 'FAILED', 'DONE').
        """
        return self._tasks.get(task_id, State.FAILED)

    def change_task_state(self, task_id: str, state: State) -> None:
        """
        Change state of the task by ID.

        Args:
            task_id (str): ID of the target task.

        Returns:
            str: state ('RUNNING', 'FAILED', 'DONE').
        """
        self._tasks[task_id] = state
