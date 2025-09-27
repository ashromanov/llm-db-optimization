"""
Response models for LLM service.
"""

from pydantic import BaseModel, Field


class DDLStatement(BaseModel):
    """
    Represents DDL statement, which will create new table.

    Attributes:
        statement (str): DDL statement itself.

    Examples:
    ```
    {
        "statement":"CREATE TABLE t1..."
    }
    ```
    """

    statement: str = Field(
        ...,
        description="DDL statement itself.",
        example="CREATE TABLE t1...",
    )


class MigrationStatement(BaseModel):
    """
    SQL query which tells how to transfer data from old tables to new ones.

    Attributes:
        statement (str): SQL command for migration.

    Examples:
    ```
    {
        "statement": "INSERT INTO T1 SELECT * FROM OldT1 LEFT JOIN ..."
    }
    ```
    """

    statement: str = Field(
        ...,
        description="SQL command for migration.",
        example="INSERT INTO T1 SELECT * FROM OldT1 LEFT JOIN ...",
    )


class OptimizedQuery(BaseModel):
    """
    Optimized SQL query from input data.

    Attributes:
        queryid (str): Unique ID of the query.
        query (str): Optimized SQL query.

    Examples:
    ```
    {
        "queryid":"10ba3c04-0f91-4ef3-a717-c1e0d33b31bc",
        "query":"WITH (...",
    }
    ```
    """

    queryid: str = Field(
        ...,
        description="Unique ID of the query.",
        example="10ba3c04-0f91-4ef3-a717-c1e0d33b31bc",
    )
    query: str = Field(
        ...,
        description="Optimized SQL query.",
        example="WITH MonthlyFlightCounts AS (SELECT ...)",
    )


class OptimizationResponse(BaseModel):
    """
    Response which will be used to optimize DB.

    Attributes:
        ddl (list[DDLStatement]): List of DDL statements, describing how DB was created.
        migrations (list[MigrationStatement]): List of SQL migration statements.
        queries (list[OptimizedQuery]): List of optimized SQL queries.
    """

    ddl: list[DDLStatement] = Field(
        ...,
        description="List of DDL statements to create new tables for optimizations.",
    )
    migrations: list[MigrationStatement] = Field(
        ...,
        description="List of sql statements to transfer data from old tables to new ones.",
    )
    queries: list[OptimizedQuery] = Field(
        ...,
        description="List of optimized SQL queries.",
    )


class TaskIdResponse(BaseModel):
    """
    Model for responding to task creation.

    Attributes:
        taskid (str): ID of newly created task.
    """

    taskid: str = Field(...)


class TaskStatusResponse(BaseModel):
    """
    Model for providing status of some task.

    Attributes:
        status (str): Status of the task.
    """

    status: str = Field(...)
