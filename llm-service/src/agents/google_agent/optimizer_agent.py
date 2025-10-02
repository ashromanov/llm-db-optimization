import asyncio
import json
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from . import prompts


# ---------------------------
# State definition
# ---------------------------
class State(TypedDict):
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
class GoogleOptimizerAgent:
    MODEL_NAME = "openai/gpt-oss-20b"

    def __init__(self, openrouter_api_key: str, temperature: float = 0.0):
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            model=self.MODEL_NAME,
            temperature=temperature,
        )
        self.graph = self.build_graph()

    # -------- Graph construction --------
    def build_graph(self):
        """
        Construct final agent graph.
        """
        workflow = StateGraph(State)

        # Add nodes
        workflow.add_node("sort_queries_by_total_time", self.sort_queries_by_total_time)
        workflow.add_node("create_new_ddl_statements", self.create_new_ddl_statements)
        workflow.add_node("create_migrations", self.create_migrations)
        workflow.add_node("optimize_queries", self.optimize_queries)
        workflow.add_node("form_final_output", self.form_final_output)

        # Add edges between nodes
        workflow.add_edge(START, "sort_queries_by_total_time")
        workflow.add_edge("sort_queries_by_total_time", "create_new_ddl_statements")
        workflow.add_edge("create_new_ddl_statements", "create_migrations")
        workflow.add_edge("create_migrations", "optimize_queries")
        workflow.add_edge("optimize_queries", "form_final_output")
        workflow.add_edge("form_final_output", END)

        return workflow.compile()

    # -------- Helper utilities --------
    def _strip_markdown_and_clean(self, text: str) -> str:
        """
        Remove markdown code blocks and clean SQL output.

        Args:
            text (str): Input text.

        Returns:
            str: Cleaned text.
        """
        # Remove markdown code blocks
        text = re.sub(r"^```[\w]*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n```$", "", text, flags=re.MULTILINE)
        text = text.replace("```", "")

        # Remove SQL comments
        text = re.sub(r"--[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]

        # Filter out empty lines and non-SQL lines WITHOUT DROP
        sql_keywords = [
            "CREATE",
            "ALTER",
            "INSERT",
            "UPDATE",
            "DELETE",
            "SELECT",
            "ALTER",
        ]
        lines = [
            line
            for line in lines
            if line and any(line.upper().startswith(kw) for kw in sql_keywords)
        ]
        return "\n".join(lines)

    def _split_clean(self, text: str) -> list[str]:
        """
        Split and clean SQL statements.

        Args:
            text (str): Text to be split in lines.

        Returns:
            list[str]: Cleaned lines from input text.
        """
        cleaned = self._strip_markdown_and_clean(text)
        return [line.strip() for line in cleaned.split("\n")]

    async def _invoke_llm(self, prompt: str) -> str:
        result = await self.llm.ainvoke(prompt)
        return result.content

    # -------- Nodes --------
    def sort_queries_by_total_time(self, state: State) -> State:
        """
        Sort by (runquantity * executiontime) descending.
        Missing values treated as zero.
        """
        print("sort_queries_by_total_time")
        state["queries"] = sorted(
            state["queries"],
            key=lambda q: q["runquantity"] * q["executiontime"],
            reverse=True,
        )
        return state

    async def create_new_ddl_statements(self, state: State) -> State:
        print("create_new_ddl_statements")
        ddl_statements = "\n".join(state["ddl_statements"])
        queries_block = "\n".join(
            [
                (
                    f"Execution time: {q.get('executiontime')}\n"
                    f"Run quantity: {q.get('runquantity')}\n"
                    f"Query:\n{q.get('query')}"
                )
                for q in state["queries"][:10]
            ]
        )
        prompt_text = prompts.CREATE_NEW_DDL_STATEMENTS.format(
            ddl_statements=ddl_statements,
            queries=queries_block,
        )
        result = await self._invoke_llm(prompt_text)
        state["out_ddl_statements"] = self._split_clean(result)
        return state

    async def create_migrations(self, state: State) -> State:
        print("create_migrations")
        old_ddl = "\n".join(state["ddl_statements"])
        new_ddl = "\n".join(state["out_ddl_statements"])
        prompt_text = prompts.CREATE_MIGRATIONS.format(
            old_ddl=old_ddl,
            new_ddl=new_ddl,
        )
        result = await self._invoke_llm(prompt_text)
        state["out_migrations"] = self._split_clean(result)
        return state

    async def optimize_queries(self, state: State) -> State:
        print("optimize_queries")

        migrations = "\n".join(state["out_migrations"])

        async def _process_query(q: dict[str, Any]) -> dict[str, str]:
            prompt_text = prompts.OPTIMIZE_QUERY.format(
                migrations=migrations,
                query=q["query"],
            )
            raw_query = await self._invoke_llm(prompt_text)
            new_query = self._strip_markdown_and_clean(raw_query)
            return {
                "queryid": q["queryid"],
                "query": new_query,
            }

        tasks = [_process_query(q) for q in state["queries"]]
        state["out_queries"] = await asyncio.gather(*tasks)
        return state

    def form_final_output(self, state: State) -> dict:
        print("form_final_output")
        return {
            "out_ddl_statements": state["out_ddl_statements"],
            "out_migrations": state["out_migrations"],
            "out_queries": state["out_queries"],
        }

    # -------- Public API --------
    async def run(self, data: dict) -> dict:
        initial_state = State(
            metadata=data["metadata"],
            ddl_statements=data["ddl_statements"],
            queries=data["queries"],
        )
        final_state = await self.graph.ainvoke(initial_state)
        print(json.dumps(final_state.get("form_final_output", final_state)))
        return final_state.get("form_final_output", final_state)


# agent = GoogleOptimizerAgent(openrouter_api_key="YOUR_API_KEY_HERE")
