"""
Service to manage tasks and their states.
"""

import uuid
from enum import Enum

from src.api.schemas.response import OptimizationResponse


class State(Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DONE = "DONE"


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, State] = {}
        self._tasks_results: dict[str, OptimizationResponse] = {}

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
    def get_task_state(self, task_id: str) -> State:
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
            state (State)
        """
        self._tasks[task_id] = state

    def set_task_result(self, task_id: str, result: OptimizationResponse) -> None:
        self._tasks_results[task_id] = result

    def get_task_result(self, task_id: str) -> OptimizationResponse | None:
        return self._tasks_results.get(task_id, None)
