import uuid

from fastapi import APIRouter

from src.api.schemas.request import DatabaseMetadata
from src.api.schemas.response import (
    DDLStatement,
    MigrationStatement,
    OptimizationResponse,
    OptimizedQuery,
    TaskIdResponse,
    TaskStatusResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/new", response_model=TaskIdResponse)
async def create_task(db_metadata: DatabaseMetadata) -> dict[str, str]:
    """
    Process creation of a new task.

    Args:
        db_metadata (DatabaseMetadata): Data which will be used by an LLM agent.

    Returns:
        TaskIdResponse: JSON with key 'taskid'.
    """
    return {"taskid": "6c12bd3f-80b1-4c0a-84ab-d3160d2e8f7a"}


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(taskid: str) -> dict[str, str]:
    """
    Check status of created task by it's ID.

    Args:
        taskid (str): ID of target task.

    Returns:
        TaskStatusResponse: JSON with key 'status'.
    """
    return {"status": "RUNNING"}  # RUNNING, FAILED, DONE


@router.get("/getresult", response_model=OptimizationResponse)
async def get_task_result(taskid: str) -> OptimizationResponse:
    """
    Returns result of the task by taskid.

    Args:
        taskid (str): ID of target task.

    Returns:
        result (OptimizationResponse): Result of task execution.
    """
    ddl_statements = [
        DDLStatement(statement="CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"),
        DDLStatement(
            statement="CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, amount DECIMAL);"
        ),
    ]
    migration_statements = [
        MigrationStatement(statement="INSERT INTO users SELECT * FROM old_users;"),
        MigrationStatement(statement="INSERT INTO orders SELECT * FROM old_orders;"),
    ]
    optimized_queries = [
        OptimizedQuery(
            queryid=str(uuid.uuid4()),
            query="SELECT id, name FROM users WHERE id > 100;",
        ),
        OptimizedQuery(
            queryid=str(uuid.uuid4()),
            query="SELECT user_id, SUM(amount) FROM orders GROUP BY user_id;",
        ),
    ]
    response = OptimizationResponse(
        ddl=ddl_statements, migrations=migration_statements, queries=optimized_queries
    )
    return response
