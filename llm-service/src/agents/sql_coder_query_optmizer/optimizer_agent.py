import asyncio
import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import sqlglot
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from sqlglot.optimizer import optimize
from typing_extensions import TypedDict

from src.settings import settings

from . import prompts

# Configure logging
logger = logging.getLogger(__name__)


def ddl_list_to_schema(ddls: list[str], dialect: str = "trino") -> sqlglot.Schema:
    """
    Convert a list of DDL (CREATE TABLE) statements into a SQLGlot Schema object.

    Args:
        ddls (list[str]): List of DDL SQL strings.
        dialect (str): SQL dialect (e.g., 'mysql', 'bigquery', 'ansi').

    Returns:
        sqlglot.optimizer.schema.Schema: Schema ready for sqlglot.optimize()
    """
    tables: dict[str, dict[str, str]] = {}

    for ddl in ddls:
        expr = sqlglot.parse_one(ddl, read=dialect)
        if not isinstance(expr, sqlglot.exp.Create):
            continue

        table_name = expr.this.name
        columns = {}

        for column in expr.find_all(sqlglot.exp.ColumnDef):
            col_name = column.name
            col_type_expr = column.args.get("kind")
            col_type = col_type_expr.this if col_type_expr else "UNKNOWN"
            columns[col_name] = str(col_type).upper()

        tables[table_name] = columns

    return tables


# ---------------------------
# State definition
# ---------------------------
class State(TypedDict):
    """
    State container for query optimization workflow.
    """

    # Input
    metadata: dict[str, str]
    ddl_statements: list[str]
    queries: list[dict[str, str | int]]
    # Output
    out_ddl_statements: list[str]
    out_migrations: list[str]
    out_queries: list[dict[str, str]]


# ---------------------------
# Agent
# ---------------------------
class QueryOptimizerAgent:
    """
    Agent for optimizing SQL queries using LLM and sqlglot.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        temperature: float = 0.1,
        model_name: str = "defog/llama-3-sqlcoder-8b",
    ):
        """
        Initialize the query optimizer agent.

        Args:
            api_key (str): OpenAI API key (or vLLM compatible key).
            base_url (str): Base URL for the OpenAI-compatible API endpoint.
            temperature (float): LLM temperature parameter for response randomness.
            model_name (str): Model name to use.
        """
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=temperature,
        )
        # SQLGlot configuration defaults
        self.dialect = "trino"
        self.db = None
        self.catalog = None

        self.graph = self._build_graph()

    @staticmethod
    def _parse_jdbc_url(jdbc_url: str) -> dict[str, str | None]:
        """
        Parse JDBC URL to extract database configuration.

        Args:
            jdbc_url: JDBC connection string
                     (e.g., 'jdbc:trino://host:443?user=x&password=y')

        Returns:
            Dictionary with 'dialect', 'db', 'catalog', and 'host'.
        """
        try:
            # Remove jdbc: prefix
            if jdbc_url.startswith("jdbc:"):
                jdbc_url = jdbc_url[5:]

            # Extract dialect from scheme
            parsed = urlparse(jdbc_url)
            dialect = parsed.scheme.lower() if parsed.scheme else "trino"

            # Map common JDBC dialects to SQLGlot dialects
            dialect_mapping = {
                "postgresql": "postgres",
                "mysql": "mysql",
                "trino": "trino",
                "presto": "presto",
                "hive": "hive",
                "snowflake": "snowflake",
                "bigquery": "bigquery",
            }
            dialect = dialect_mapping.get(dialect, dialect)

            # Extract database and catalog from path
            path = parsed.path.lstrip("/")
            db = None
            catalog = None

            if path:
                parts = path.split("/")
                if len(parts) >= 1:
                    catalog = parts[0]
                if len(parts) >= 2:
                    db = parts[1]

            # Parse query parameters for additional config
            query_params = parse_qs(parsed.query)

            # Some JDBC drivers use schema/catalog in query params
            if not catalog and "catalog" in query_params:
                catalog = query_params["catalog"][0]
            if not db and "schema" in query_params:
                db = query_params["schema"][0]

            logger.info(
                f"Parsed JDBC URL - dialect: {dialect}, "
                f"catalog: {catalog}, db: {db}, host: {parsed.hostname}"
            )

            return {
                "dialect": dialect,
                "db": db,
                "catalog": catalog,
                "host": parsed.hostname,
            }

        except Exception as e:
            logger.warning(f"Failed to parse JDBC URL: {e}. Using defaults.")
            return {
                "dialect": "trino",
                "db": None,
                "catalog": None,
                "host": None,
            }

    def _build_graph(self):
        """
        Construct the agent's state graph workflow.
        """
        workflow = StateGraph(State)

        # Add nodes
        workflow.add_node("optimize_queries", self._optimize_queries_node)
        workflow.add_node("form_final_output", self._form_final_output_node)

        # Define workflow
        workflow.add_edge(START, "optimize_queries")
        workflow.add_edge("optimize_queries", "form_final_output")
        workflow.add_edge("form_final_output", END)

        return workflow.compile()

    @staticmethod
    def _clean_llm_output(text: str) -> str:
        """
        Clean LLM output by removing markdown, comments, and normalizing whitespace.

        Args:
            text: Raw LLM output text.

        Returns:
            Cleaned SQL query string.
        """
        # Remove markdown code fences
        text = re.sub(r"```(?:\w+)?", "", text)
        # Remove SQL comments (-- and /* */)
        text = re.sub(r"--[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        # Normalize whitespace
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        # Ensure semicolon termination
        if text and not text.endswith(";"):
            text += ";"
        return text

    async def _invoke_llm(self, prompt: str) -> str:
        """
        Invoke the LLM with error handling.

        Args:
            prompt: Prompt text to send to LLM.

        Returns:
            LLM response content.

        Raises:
            QueryOptimizationError: If LLM invocation fails.
        """
        try:
            result = await self.llm.ainvoke(prompt)
            return result.content
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise e

    def _validate_sql(self, query: str) -> tuple[bool, str]:
        """
        Validate SQL query syntax using sqlglot.

        Args:
            query: SQL query string to validate.

        Returns:
            Tuple of (is_valid, error_message). error_message is empty if valid.
        """
        try:
            parsed = sqlglot.parse_one(query, read=self.dialect)
            if parsed is None:
                return False, "Failed to parse query"
            # Additional validation: try to transpile back
            parsed.sql(dialect=self.dialect)
            return True, ""
        except Exception as e:
            return False, str(e)

    def _parse_and_optimize_sql(
        self, query: str, schema: dict[str, dict[str, str]]
    ) -> tuple[str, bool]:
        """
        Parse and optimize SQL query using sqlglot with full validation.

        Args:
            query: SQL query string.
            schema: Schema dictionary for optimization.

        Returns:
            Tuple of (optimized_query, success_flag).
        """
        try:
            # Validate input query
            is_valid, error = self._validate_sql(query)
            if not is_valid:
                logger.warning(f"Input query validation failed: {error}")
                return query, False

            # Parse and optimize with full parameters
            parsed = sqlglot.parse_one(query, read=self.dialect)
            optimized = optimize(
                parsed,
                schema=schema,
                db=self.db,
                catalog=self.catalog,
                dialect=self.dialect,
            )

            # Generate SQL and validate output
            optimized_sql = optimized.sql(dialect=self.dialect).replace('"', "")
            is_valid, error = self._validate_sql(optimized_sql)

            if not is_valid:
                logger.warning(f"Optimized query validation failed: {error}")
                return query, False

            return optimized_sql, True

        except Exception as e:
            logger.error(f"SQL optimization failed: {e}")
            return query, False

    async def _process_single_query(
        self, query_data: dict[str, str], ddls: list[str]
    ) -> dict[str, str]:
        """
        Process and optimize a single query with robust fallback logic.

        Fallback chain:
        1. LLM optimization → SQLGlot validation + optimization
        2. If fails → Original query → SQLGlot validation + optimization
        3. If fails → Return original query as-is

        Args:
            query_data: Dictionary containing 'queryid' and 'query'.
            ddls: List of DDL statements for schema.

        Returns:
            Dictionary with optimized query and ID.
        """
        query_id = query_data["queryid"]
        original_query = query_data["query"]
        schema = ddl_list_to_schema(ddls, dialect=self.dialect)
        ddls_text = "\n".join(ddls)

        # Step 1: Try LLM optimization
        try:
            prompt = prompts.OPTIMIZE_QUERY.format(query=original_query, ddls=ddls_text)
            llm_response = await self._invoke_llm(prompt)
            cleaned_query = self._clean_llm_output(llm_response)

            # Validate and optimize LLM output
            optimized_query, success = self._parse_and_optimize_sql(
                cleaned_query, schema
            )

            if success:
                logger.info(f"Successfully optimized query {query_id} via LLM")
                return {"queryid": str(query_id), "query": optimized_query}

            logger.warning(f"LLM output invalid for query {query_id}, trying original")

        except Exception as e:
            logger.warning(f"LLM optimization failed for query {query_id}: {e}")

        # Step 2: Fallback to optimizing original query
        try:
            optimized_query, success = self._parse_and_optimize_sql(
                original_query, schema
            )

            if success:
                logger.info(f"Optimized original query {query_id} via SQLGlot only")
                return {"queryid": str(query_id), "query": optimized_query}

            logger.warning(
                f"Original query optimization failed for {query_id}, returning as-is"
            )

        except Exception as e:
            logger.warning(f"Fallback optimization failed for query {query_id}: {e}")

        # Step 3: Final fallback - return original unchanged
        logger.info(f"Returning original query {query_id} unchanged")
        return {"queryid": str(query_id), "query": original_query}

    async def _optimize_queries_node(self, state: State) -> State:
        """
        Graph node: Optimize all queries in parallel.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with optimized queries.
        """
        logger.info(f"Optimizing {len(state['queries'])} queries...")

        tasks = [
            self._process_single_query(q, state["ddl_statements"])
            for q in state["queries"]
        ]
        optimized_queries = await asyncio.gather(*tasks, return_exceptions=False)

        state["out_queries"] = optimized_queries
        logger.info(
            f"Optimization complete. Processed {len(optimized_queries)} queries."
        )
        return state

    @staticmethod
    def _form_final_output_node(state: State) -> dict[str, Any]:
        """
        Graph node: Format final output from state.

        Args:
            state: Current workflow state.

        Returns:
            Output dictionary with results.
        """
        logger.info("Forming final output")
        return {
            "out_ddl_statements": state.get("out_ddl_statements", []),
            "out_migrations": state.get("out_migrations", []),
            "out_queries": state["out_queries"],
        }

    async def run(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Run the optimization agent on input data.

        Args:
            data: Input dictionary with 'metadata', 'ddl_statements', and 'queries'.
                  metadata can be either a JDBC URL string or a dict with connection info.

        Returns:
            Dictionary containing optimization results.

        Raises:
            ValueError: If required input fields are missing.
        """
        # Extract SQLGlot configuration from metadata
        metadata = data.get("metadata", {})

        # Handle metadata as JDBC URL string or dict
        if isinstance(metadata, str):
            # metadata is a JDBC URL
            jdbc_config = self._parse_jdbc_url(metadata)
            self.dialect = jdbc_config["dialect"]
            self.db = jdbc_config["db"]
            self.catalog = jdbc_config["catalog"]
        elif isinstance(metadata, dict):
            # metadata is a dictionary (legacy support)
            self.dialect = metadata.get("dialect", "trino")
            self.db = metadata.get("db")
            self.catalog = metadata.get("catalog")
        else:
            # Default values
            logger.warning("Invalid metadata format. Using default configuration.")
            self.dialect = "trino"
            self.db = None
            self.catalog = None

        logger.info(
            f"SQLGlot config - dialect: {self.dialect}, "
            f"db: {self.db}, catalog: {self.catalog}"
        )

        # Initialize state with proper typing
        initial_state: State = {
            "metadata": data["metadata"],
            "ddl_statements": data["ddl_statements"],
            "queries": data["queries"],
            "out_ddl_statements": [],
            "out_migrations": [],
            "out_queries": [],
        }

        # Run workflow
        final_state = await self.graph.ainvoke(initial_state)

        # Extract results (form_final_output node returns dict directly)
        result = final_state.get("form_final_output", final_state)

        logger.debug(f"Final result: {json.dumps(result, indent=2)}")
        return result


# Initialize singleton agent instance
agent = QueryOptimizerAgent(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)
