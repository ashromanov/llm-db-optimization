import asyncio

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.agents.query_optimizer.optimizer_agent import agent
from src.api.schemas.request import DatabaseMetadata
from src.api.schemas.response import (
    OptimizationResponse,
    TaskIdResponse,
    TaskStatusResponse,
)
from src.services.task_manager import TaskManager

router = APIRouter(prefix="", tags=["tasks"], route_class=DishkaRoute)


@router.post("/new", response_model=TaskIdResponse)
async def create_task(
    db_metadata: DatabaseMetadata,
    task_manager: FromDishka[TaskManager],
) -> dict[str, str]:
    """
    Process creation of a new task.

    Args:
        db_metadata (DatabaseMetadata): Data which will be used by an LLM agent.

    Returns:
        TaskIdResponse: JSON with key 'taskid'.
    """
    data = db_metadata.to_agent_input()
    task = asyncio.create_task(agent.run(data))
    taskid = task_manager.add_task(task)
    return TaskIdResponse(taskid=taskid)


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str, task_manager: FromDishka[TaskManager]
) -> dict[str, str]:
    """
    Check status of created task by it's ID.

    Args:
        taskid (str): ID of target task.

    Returns:
        TaskStatusResponse: JSON with key 'status'.
    """
    status = task_manager.get_status(task_id)
    return TaskStatusResponse(status=status)


@router.get("/getresult", response_model=OptimizationResponse)
async def get_task_result(task_id: str, task_manager: FromDishka[TaskManager]):
    """
    Returns result of the task by taskid.

    Args:
        taskid (str): ID of target task.

    Returns:
        result (OptimizationResponse): Result of task execution.
    """
    result = task_manager.get_result(task_id)

    if not result:
        raise HTTPException(status_code=404, detail="Not found task result")

    response = OptimizationResponse.from_agent_response(result)
    return response
