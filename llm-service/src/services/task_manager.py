import asyncio
import time
import uuid
from enum import StrEnum

from loguru import logger


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class Status(StrEnum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DONE = "DONE"


class TrackedTask:
    def __init__(self, task: asyncio.Task):
        self.id = str(uuid.uuid4())
        self._task = task
        self.status = Status.RUNNING
        self.result: dict | None = None
        self.error: str | None = None
        self.created_at: float = time.monotonic()


class TaskManager:
    def __init__(self, ttl: int = 3600, cleanup_interval: int = 300):
        self._tasks: dict[str, TrackedTask] = {}
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: asyncio.Task | None = None

    def add_task(self, task: asyncio.Task) -> str:
        tracked = TrackedTask(task)
        self._tasks[tracked.id] = tracked
        logger.info(f"Task {tracked.id} created")
        return tracked.id

    def get_status(self, task_id: str) -> Status:
        tracked = self._get_tracked(task_id)

        if tracked.status == Status.RUNNING and tracked._task.done():
            try:
                tracked.result = tracked._task.result()
                tracked.status = Status.DONE
            except Exception as e:
                tracked.status = Status.FAILED
                tracked.error = str(e)
                logger.error(f"Task {task_id} failed: {e}")

        return tracked.status

    def get_result(self, task_id: str) -> dict:
        tracked = self._get_tracked(task_id)

        self.get_status(task_id)

        if tracked.status == Status.FAILED:
            raise RuntimeError(f"Task {task_id} failed: {tracked.error}")
        if tracked.result is None:
            raise RuntimeError(f"Task {task_id} is still running")

        return tracked.result

    def _get_tracked(self, task_id: str) -> TrackedTask:
        tracked = self._tasks.get(task_id)
        if tracked is None:
            raise TaskNotFoundError(task_id)
        return tracked

    async def start_cleanup_loop(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_loop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self._cleanup_interval)
            self._cleanup_expired()

    def _cleanup_expired(self):
        now = time.monotonic()
        expired = [
            tid
            for tid, t in self._tasks.items()
            if now - t.created_at > self._ttl and t._task.done()
        ]
        for tid in expired:
            del self._tasks[tid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tasks")
