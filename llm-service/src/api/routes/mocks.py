import json
import uuid

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.api.schemas.request import DatabaseMetadata
from src.api.schemas.response import (
    DDLStatement,
    MigrationStatement,
    OptimizationResponse,
    OptimizedQuery,
    TaskIdResponse,
    TaskStatusResponse,
)
from src.services.task_manager import Status, TaskManager

MOCK_FLIGHTS_DATA = None
MOCK_QUESTS_DATA = None

with open("./src/mocks/result_flights.json") as file:
    MOCK_FLIGHTS_DATA = json.load(file)

with open("./src/mocks/result_quests.json") as file:
    MOCK_QUESTS_DATA = json.load(file)


router = APIRouter(prefix="/mocks", tags=["mocks"], route_class=DishkaRoute)


@router.post("/new", response_model=TaskIdResponse)
async def create_task(
    db_metadata: DatabaseMetadata, task_manager: FromDishka[TaskManager]
) -> dict[str, str]:
    """
    Process creation of a new task.

    Args:
        db_metadata (DatabaseMetadata): Data which will be used by an LLM agent.

    Returns:
        TaskIdResponse: JSON with key 'taskid'.
    """

    #task_id = task_manager.create_task()

    # Что то делаем с task_id надо типо в background task просто кинуть и кайфовать

    return {"taskid": "123"}


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(
    taskid: str, task_manager: FromDishka[TaskManager]
) -> dict[str, str]:
    """
    Check status of created task by it's ID.

    Args:
        taskid (str): ID of target task.

    Returns:
        TaskStatusResponse: JSON with key 'status'.
    """

    task_manager.get_status(taskid, Status.DONE)

    return {"status": Status.DONE}


@router.get("/getresult", response_model=OptimizationResponse)
async def get_task_result(
    taskid: str, task_manager: FromDishka[TaskManager]
) -> OptimizationResponse:
    """
    Returns result of the task by taskid.

    Args:
        taskid (str): ID of target task.

    Returns:
        result (OptimizationResponse): Result of task execution.
    """
    # ddl_statements = [
    #     DDLStatement(statement="CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"),
    #     DDLStatement(
    #         statement="CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, amount DECIMAL);"
    #     ),
    # ]
    # migration_statements = [
    #     MigrationStatement(statement="INSERT INTO users SELECT * FROM old_users;"),
    #     MigrationStatement(statement="INSERT INTO orders SELECT * FROM old_orders;"),
    # ]
    # optimized_queries = [
    #     OptimizedQuery(
    #         queryid=str(uuid.uuid4()),
    #         query="SELECT id, name FROM users WHERE id > 100;",
    #     ),
    #     OptimizedQuery(
    #         queryid=str(uuid.uuid4()),
    #         query="SELECT user_id, SUM(amount) FROM orders GROUP BY user_id;",
    #     ),
    # ]
    # response = OptimizationResponse(
    #     ddl=ddl_statements, migrations=migration_statements, queries=optimized_queries
    # )

    # response = task_manager.get_task_result(taskid)

    # if not response:
    #     raise HTTPException(status_code=404, detail="Not found task result")

    return MOCK_QUESTS_DATA
