import asyncio
import json
import logging
import re
from typing import Any

import sqlglot
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from sqlglot.optimizer import optimize
from typing_extensions import TypedDict

from src.settings import settings

from . import prompts

# Configure logging
logger = logging.getLogger(__name__)


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
        google_api_key: str,
        temperature: float = 0.2,
        model_name: str = "gemini-2.5-pro",
    ):
        """
        Initialize the query optimizer agent.

        Args:
            google_api_key (srt): Google API key. If None, reads from GOOGLE_API_KEY env var.
            temperature (float): LLM temperature parameter for response randomness.
        """
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=model_name,
            temperature=temperature,
        )
        self.graph = self._build_graph()

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

    def _parse_and_optimize_sql(self, query: str) -> str:
        """
        Parse and optimize SQL query using sqlglot.

        Args:
            query (str): SQL query string.

        Returns:
            str: Optimized SQL query string.

        Raises:
            SQLParseError: If SQL parsing fails.
        """
        try:
            parsed = sqlglot.parse_one(query, read="trino")
            optimized = optimize(parsed)
            return str(optimized)
        except Exception as e:
            logger.error(
                f"SQL parsing/optimization failed for query: {query};Error: {e}"
            )
            raise Exception(f"Failed to parse/optimize SQL: {e}") from e

    async def _process_single_query(self, query_data: dict[str, str]) -> dict[str, str]:
        """
        Process and optimize a single query.

        Args:
            query_data (dict[str, str]): Dictionary containing 'queryid' and 'query'.

        Returns:
            Dictionary with optimized query and ID.
        """
        query_id = query_data["queryid"]
        original_query = query_data["query"]

        try:
            # Get LLM optimization suggestion
            prompt = prompts.OPTIMIZE_QUERY.format(query=original_query)
            llm_response = await self._invoke_llm(prompt)

            # Clean and parse LLM output
            cleaned_query = self._clean_llm_output(llm_response)

            # Apply sqlglot optimization twice: once for pretty formatting, once for final
            pretty_optimized = self._parse_and_optimize_sql(cleaned_query)
            final_optimized = self._parse_and_optimize_sql(pretty_optimized)

            logger.info(f"Successfully optimized query {query_id}")
            return {
                "queryid": str(query_id),
                "query": final_optimized,
            }
        except Exception as e:
            logger.warning(
                f"Failed to optimize query {query_id}: {e}. Returning original."
            )
            # Fallback to original query on error
            return {
                "queryid": str(query_id),
                "query": original_query,
            }

    async def _optimize_queries_node(self, state: State) -> State:
        """
        Graph node: Optimize all queries in parallel.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with optimized queries.
        """
        logger.info(f"Optimizing {len(state['queries'])} queries...")

        tasks = [self._process_single_query(q) for q in state["queries"]]
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

        Returns:
            Dictionary containing optimization results.

        Raises:
            ValueError: If required input fields are missing.
        """
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


agent = QueryOptimizerAgent(google_api_key=settings.google_api_key)
