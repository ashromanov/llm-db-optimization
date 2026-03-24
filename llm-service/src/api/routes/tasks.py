import asyncio

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.agents.pipeline.orchestrator import PipelineOptimizer
from src.api.schemas.request import DatabaseMetadata
from src.api.schemas.response import (
    OptimizationResponse,
    TaskIdResponse,
    TaskStatusResponse,
)
from src.services.task_manager import TaskManager, TaskNotFoundError

router = APIRouter(prefix="", tags=["tasks"], route_class=DishkaRoute)


@router.post("/new", response_model=TaskIdResponse)
async def create_task(
    db_metadata: DatabaseMetadata,
    task_manager: FromDishka[TaskManager],
    optimizer: FromDishka[PipelineOptimizer],
) -> TaskIdResponse:
    data = db_metadata.to_agent_input()
    task = asyncio.create_task(optimizer.run(data))
    taskid = task_manager.add_task(task)
    return TaskIdResponse(taskid=taskid)


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_manager: FromDishka[TaskManager],
) -> TaskStatusResponse:
    try:
        status = task_manager.get_status(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(status=status)


@router.get("/getresult", response_model=OptimizationResponse)
async def get_task_result(
    task_id: str,
    task_manager: FromDishka[TaskManager],
) -> OptimizationResponse:
    try:
        result = task_manager.get_result(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return OptimizationResponse.from_agent_response(result)
