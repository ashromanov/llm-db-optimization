"""
Request models for LLM service.
"""

from pydantic import BaseModel, Field


class DDLStatement(BaseModel):
    """
    Represents DDL statement, which creates table.

    Attributes:
        statement (str): DDL statement itself.

    Examples:
    ```
    {
        "statement": "CREATE TABLE Table1.........",
    }
    ```
    """

    statement: str = Field(
        ...,
        description="DDL statement itself.",
        example="CREATE TABLE Table1 (id INT PRIMARY KEY, name VARCHAR(100));",
    )


class QueryDetails(BaseModel):
    """
    SQL query with details such as run quantity and execution time.

    Attributes:
        queryid (str): Unique ID of the query.
        query (str): SQL query itself.
        runquantity (int): How many times this query will be run.
        executiontime (int): How much time did it take to run query before optimizations.

    Examples:
    ```
    {
        "queryid":"10ba3c04-0f91-4ef3-a717-c1e0d33b31bc",
        "query":"WITH MonthlyFlightCounts AS ( SELECT...",
        "runquantity": 795,
        "executiontime": 20
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
        description="The SQL query text.",
        example="WITH MonthlyFlightCounts AS (SELECT ...)",
    )
    runquantity: int = Field(
        ..., description="How many times this query will be run.", ge=0, example=795
    )
    executiontime: int = Field(
        ...,
        description="Execution time (in seconds) before optimizations.",
        ge=0,
    )


class DatabaseMetadata(BaseModel):
    """
    Model for the entire dataset provided to the service.

    Attributes:
        url (str): Connection string for the db.
        ddl (list[DDLStatement]): List of DDL statements, describing how DB was created.
        queries (list[QueryDetails]): List of most run queries which need to be optomized.
    """

    url: str = Field(
        ...,
        description="Connection string for the database.",
        example="postgresql://user:pass@localhost:5432/mydb",
    )
    ddl: list[DDLStatement] = Field(
        ..., description="List of DDL statements describing how the DB was created."
    )
    queries: list[QueryDetails] = Field(
        ..., description="List of frequently run queries that need to be optimized."
    )

    def to_agent_input(self) -> dict:
        """
        Converts model to AI agent compatible dict.
        """
        metadata = {"url": self.url}
        ddl_statements = [ddl.statement for ddl in self.ddl]
        queries = [
            {
                "queryid": q.queryid,
                "query": q.query,
                "runquantity": q.runquantity,
                "executiontime": q.executiontime,
            }
            for q in self.queries
        ]

        return {
            "metadata": metadata,
            "ddl_statements": ddl_statements,
            "queries": queries,
        }
