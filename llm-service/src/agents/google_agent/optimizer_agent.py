import asyncio
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from . import prompts


# ---------------------------
# State definition
# ---------------------------
class State(TypedDict, total=False):
    # Input
    input_metadata: dict[str, str]
    input_ddl_statements: list[str]
    input_queries: list[dict[str, Any]]
    # Output
    output_ddl_statements: list[str]
    output_migrations: list[str]
    output_queries: list[dict[str, Any]]


# ---------------------------
# Agent
# ---------------------------
class GoogleOptimizerAgent:
    MODEL_NAME = "gemini-2.5-pro"

    def __init__(self, google_api_key: str, temperature: float = 0.5):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=self.MODEL_NAME,
            temperature=temperature,
        )
        self.chain = self.build_chain()

    # -------- Graph construction --------
    def build_chain(self):
        workflow = StateGraph(State)

        workflow.add_node("sort_queries_by_total_time", self.sort_queries_by_total_time)
        workflow.add_node("create_new_ddl_statements", self.create_new_ddl_statements)
        workflow.add_node("create_migrations", self.create_migrations)
        workflow.add_node("optimize_queries", self.optimize_queries)
        workflow.add_node("form_final_output", self.form_final_output)

        workflow.add_edge(START, "sort_queries_by_total_time")
        workflow.add_edge("sort_queries_by_total_time", "create_new_ddl_statements")
        workflow.add_edge("create_new_ddl_statements", "create_migrations")
        workflow.add_edge("create_migrations", "optimize_queries")
        workflow.add_edge("optimize_queries", "form_final_output")
        workflow.add_edge("form_final_output", END)

        return workflow.compile()

    # -------- Helper utilities --------
    @staticmethod
    def _safe_product(a: Any, b: Any) -> float:
        try:
            return float(a) * float(b)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _split_clean(text: str) -> list[str]:
        return [line.strip() for line in text.strip().splitlines() if line.strip()]

    async def _invoke_llm(self, prompt: str) -> str:
        result = await self.llm.ainvoke(prompt)
        return result.content.strip()

    # -------- Nodes --------
    def sort_queries_by_total_time(self, state: State) -> State:
        """
        Sort by (runquantity * executiontime) descending.
        Missing values treated as zero.
        """
        print("sort_queries_by_total_time")
        state["input_queries"] = sorted(
            state["input_queries"],
            key=lambda q: self._safe_product(
                q.get("runquantity"), q.get("executiontime")
            ),
            reverse=True,
        )
        return state

    async def create_new_ddl_statements(self, state: State) -> State:
        print("create_new_ddl_statements")
        ddl_statements = "\n".join(state["input_ddl_statements"])
        queries_block = "\n\n".join(
            [
                (
                    f"Execution time: {q.get('executiontime')}\n"
                    f"Run quantity: {q.get('runquantity')}\n"
                    f"Query:\n{q.get('query')}"
                )
                for q in state["input_queries"][:10]
            ]
        )
        prompt_text = prompts.CREATE_NEW_DDL_STATEMENTS.format(
            input_ddl_statements=ddl_statements,
            input_queries=queries_block,
        )
        result = await self._invoke_llm(prompt_text)
        state["output_ddl_statements"] = self._split_clean(result)
        return state

    async def create_migrations(self, state: State) -> State:
        print("create_migrations")
        old_ddl = "\n".join(state["input_ddl_statements"])
        new_ddl = "\n".join(state["output_ddl_statements"])
        prompt_text = prompts.CREATE_MIGRATIONS.format(
            input_ddl_statements=old_ddl,
            output_ddl_statements=new_ddl,
        )
        result = await self._invoke_llm(prompt_text)
        state["output_migrations"] = self._split_clean(result)
        return state

    async def optimize_queries(self, state: State) -> State:
        print("optimize_queries")
        migration_text = "\n".join(state["output_migrations"])

        async def _opt_single(q: dict[str, Any]) -> dict[str, Any]:
            prompt_text = prompts.OPTIMIZE_QUERY.format(
                migration_commands=migration_text,
                query=q.get("query", ""),
            )
            new_query = await self._invoke_llm(prompt_text)
            query_id = q.get("queryid") or q.get("id") or q.get("query_hash") or ""
            return {"queryid": query_id, "optimized_query": new_query}

        semaphore = asyncio.Semaphore(10)

        async def _wrapped(q):
            async with semaphore:
                return await _opt_single(q)

        tasks = [_wrapped(q) for q in state["input_queries"]]
        state["output_queries"] = await asyncio.gather(*tasks)
        return state

    def form_final_output(self, state: State) -> dict:
        print("form_final_output")
        return {
            "output_ddl_statements": state.get("output_ddl_statements", []),
            "output_migrations": state.get("output_migrations", []),
            "output_queries": state.get("output_queries", []),
        }

    # -------- Public API --------
    async def run(
        self,
        input_ddl_statements: list[str],
        input_queries: list[dict[str, Any]],
        input_metadata: dict[str, str] | None = None,
    ) -> dict:
        initial_state: State = {
            "input_metadata": input_metadata or {},
            "input_ddl_statements": input_ddl_statements,
            "input_queries": input_queries,
        }
        final_state = await self.chain.ainvoke(initial_state)
        return final_state.get("form_final_output", final_state)
