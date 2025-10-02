"""
Google Optimizer Agent - Multi-agent pipeline for database optimization.
"""

import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from src.settings import settings

from .analyst_agent import AnalystAgent
from .ddl_agent import DDLAgent
from .migration_agent import MigrationAgent
from .query_agent import QueryAgent


# ---------------------------
# State definition
# ---------------------------
class State(TypedDict):
    # Input
    metadata: dict[str, str]
    ddl_statements: list[str]
    queries: list[dict[str, str | int]]
    # Intermediate
    optimization_plan: str
    # Output
    out_ddl_statements: list[str]
    out_migrations: list[str]
    out_queries: list[dict[str, str]]


# ---------------------------
# Main Agent Pipeline
# ---------------------------
class GoogleOptimizerAgent:
    """
    Multi-agent pipeline for Trino database optimization.
    """

    def __init__(self, google_api_key: str):
        """
        Initialize the optimizer agent pipeline.

        Args:
            google_api_key: Google API key for Gemini models.
        """
        print("[GoogleOptimizerAgent] Initializing...")

        # Initialize sub-agents
        self.analyst_agent = AnalystAgent(
            google_api_key=google_api_key, temperature=0.2
        )
        self.ddl_agent = DDLAgent(google_api_key=google_api_key, temperature=0.0)
        self.migration_agent = MigrationAgent(
            google_api_key=google_api_key, temperature=0.0
        )
        self.query_agent = QueryAgent(google_api_key=google_api_key, temperature=0.0)

        # Build pipeline graph
        self.graph = self.build_graph()

        print("[GoogleOptimizerAgent] ✓ Pipeline initialized with 4 agents")

    # -------- Graph construction --------
    def build_graph(self):
        """
        Construct the agent pipeline graph.
        """
        workflow = StateGraph(State)

        # Add nodes
        workflow.add_node("sort_queries_by_total_time", self.sort_queries_by_total_time)
        workflow.add_node("analyze_schema", self.analyze_schema)
        workflow.add_node("develop_ddl", self.develop_ddl)
        workflow.add_node("generate_migrations", self.generate_migrations)
        workflow.add_node("optimize_queries", self.optimize_queries)
        workflow.add_node("form_final_output", self.form_final_output)

        # Add edges
        workflow.add_edge(START, "sort_queries_by_total_time")
        workflow.add_edge("sort_queries_by_total_time", "analyze_schema")
        workflow.add_edge("analyze_schema", "develop_ddl")
        workflow.add_edge("develop_ddl", "generate_migrations")
        workflow.add_edge("generate_migrations", "optimize_queries")
        workflow.add_edge("optimize_queries", "form_final_output")
        workflow.add_edge("form_final_output", END)

        return workflow.compile()

    # -------- Pipeline Nodes --------

    def sort_queries_by_total_time(self, state: State) -> State:
        """
        Sort queries by impact (runquantity × executiontime) descending.
        """
        print("\n[1/6] Sorting queries by impact...")

        state["queries"] = sorted(
            state["queries"],
            key=lambda q: q.get("runquantity", 0) * q.get("executiontime", 0),
            reverse=True,
        )

        print(f"[1/6] ✓ Sorted {len(state['queries'])} queries")
        return state

    async def analyze_schema(self, state: State) -> State:
        """
        Analyze schema and queries, create optimization plan.
        """
        print("\n[2/6] Running AnalystAgent...")

        optimization_plan = await self.analyst_agent.analyze(
            ddl_statements=state["ddl_statements"],
            queries=state["queries"],
        )

        state["optimization_plan"] = optimization_plan

        print("[2/6] ✓ Optimization plan created")
        print(f"[2/6] Plan preview (first 100 chars):\n{optimization_plan[:100]}...\n")

        return state

    async def develop_ddl(self, state: State) -> State:
        """
        Develop mogration statements.
        """
        print("\n[3/6] Running DeveloperAgent for DDL...")

        new_ddl_statements = await self.ddl_agent.develop_ddl(
            optimization_plan=state["optimization_plan"],
            original_ddl_statements=state["ddl_statements"],
        )

        state["out_ddl_statements"] = new_ddl_statements

        print(f"[3/6] ✓ Generated {len(new_ddl_statements)} DDL statements")

        return state

    async def generate_migrations(self, state: State) -> State:
        """
        Generate migration statements from plan.
        """
        print("\n[4/6] Running MigrationAgent...")

        migration_statements = await self.migration_agent.generate_migrations(
            optimization_plan=state["optimization_plan"],
            old_ddl_statements=state["ddl_statements"],
            new_ddl_statements=state["out_ddl_statements"],
        )

        state["out_migrations"] = migration_statements

        print(f"[4/6] ✓ Generated {len(migration_statements)} migration statements")

        return state

    async def optimize_queries(self, state: State) -> State:
        """
        Rewrite all queries for new schema in parallel.
        """
        print("\n[5/6] Running QueryOptimizerAgent (Gemini 2.5 Flash)...")
        print(f"[5/6] Optimizing {len(state['queries'])} queries in parallel...")

        async def _process_query(q: dict[str, Any]) -> dict[str, str]:
            optimized_query = await self.query_agent.optimize_query(
                query=q["query"],
                migration_commands=state["out_migrations"],
            )
            return {
                "queryid": q["queryid"],
                "query": optimized_query,
            }

        # Process all queries in parallel
        tasks = [_process_query(q) for q in state["queries"]]
        state["out_queries"] = await asyncio.gather(*tasks)

        print(f"[5/6] ✓ Optimized {len(state['out_queries'])} queries")

        return state

    def form_final_output(self, state: State) -> dict:
        """
        Form final output dictionary.
        """
        print("\n[6/6] Forming final output...")

        result = {
            "out_ddl_statements": state["out_ddl_statements"],
            "out_migrations": state["out_migrations"],
            "out_queries": state["out_queries"],
        }

        print("[6/6] ✓ Pipeline complete!")
        print("Final results:")
        print(f"  - DDL statements: {len(result['out_ddl_statements'])}")
        print(f"  - Migrations: {len(result['out_migrations'])}")
        print(f"  - Optimized queries: {len(result['out_queries'])}")

        return result

    # -------- Public API --------

    async def run(self, data: dict) -> dict:
        """
        Run the optimization pipeline.

        Args:
            data: Input data with keys:
                - metadata: Database connection metadata
                - ddl_statements: List of DDL statements
                - queries: List of queries with metrics

        Returns:
            dict: Optimization results with keys:
                - out_ddl_statements: List of optimized DDL statements
                - out_migrations: List of migration SQL statements
                - out_queries: List of optimized queries
        """
        print("\n" + "=" * 80)
        print("GOOGLE OPTIMIZER AGENT PIPELINE")
        print("=" * 80)

        initial_state = State(
            metadata=data["metadata"],
            ddl_statements=data["ddl_statements"],
            queries=data["queries"],
            optimization_plan="",
            out_ddl_statements=[],
            out_migrations=[],
            out_queries=[],
        )

        final_state = await self.graph.ainvoke(initial_state)

        # Extract final output
        result = final_state.get("form_final_output", final_state)

        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 80 + "\n")

        # Optional: print full result as JSON
        # print(json.dumps(result, indent=2, ensure_ascii=False))

        return result


# ---------------------------
# Global agent instance
# ---------------------------
agent = GoogleOptimizerAgent(google_api_key=settings.google_api_key)
