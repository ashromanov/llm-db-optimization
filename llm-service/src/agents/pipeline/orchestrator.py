import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph
from loguru import logger
from typing_extensions import TypedDict

from src.agents.llm_factory import create_llm
from src.settings import AppSettings

from .analyst import AnalystAgent
from .ddl import DDLAgent
from .migration import MigrationAgent
from .query import QueryAgent


class State(TypedDict):
    metadata: dict[str, str]
    ddl_statements: list[str]
    queries: list[dict[str, str | int]]
    optimization_plan: str
    out_ddl_statements: list[str]
    out_migrations: list[str]
    out_queries: list[dict[str, str]]


class PipelineOptimizer:
    def __init__(self, settings: AppSettings):
        logger.info("Initializing PipelineOptimizer...")

        analyst_llm = create_llm(settings, temperature=settings.llm_analyst_temperature)
        code_llm = create_llm(settings, temperature=0.0)

        self.analyst = AnalystAgent(analyst_llm)
        self.ddl_agent = DDLAgent(code_llm)
        self.migration_agent = MigrationAgent(code_llm)
        self.query_agent = QueryAgent(code_llm)

        self.graph = self._build_graph()
        logger.info("PipelineOptimizer ready with 4 agents")

    def _build_graph(self):
        workflow = StateGraph(State)

        workflow.add_node("sort_queries", self._sort_queries)
        workflow.add_node("analyze_schema", self._analyze_schema)
        workflow.add_node("develop_ddl", self._develop_ddl)
        workflow.add_node("generate_migrations", self._generate_migrations)
        workflow.add_node("optimize_queries", self._optimize_queries)
        workflow.add_node("form_output", self._form_output)

        workflow.add_edge(START, "sort_queries")
        workflow.add_edge("sort_queries", "analyze_schema")
        workflow.add_edge("analyze_schema", "develop_ddl")
        workflow.add_edge("develop_ddl", "generate_migrations")
        workflow.add_edge("generate_migrations", "optimize_queries")
        workflow.add_edge("optimize_queries", "form_output")
        workflow.add_edge("form_output", END)

        return workflow.compile()

    def _sort_queries(self, state: State) -> State:
        logger.info(f"[1/6] Sorting {len(state['queries'])} queries by impact...")
        state["queries"] = sorted(
            state["queries"],
            key=lambda q: q.get("runquantity", 0) * q.get("executiontime", 0),
            reverse=True,
        )
        return state

    async def _analyze_schema(self, state: State) -> State:
        logger.info("[2/6] Running AnalystAgent...")
        state["optimization_plan"] = await self.analyst.analyze(
            ddl_statements=state["ddl_statements"],
            queries=state["queries"],
        )
        return state

    async def _develop_ddl(self, state: State) -> State:
        logger.info("[3/6] Running DDLAgent...")
        state["out_ddl_statements"] = await self.ddl_agent.develop_ddl(
            optimization_plan=state["optimization_plan"],
            original_ddl_statements=state["ddl_statements"],
        )
        return state

    async def _generate_migrations(self, state: State) -> State:
        logger.info("[4/6] Running MigrationAgent...")
        state["out_migrations"] = await self.migration_agent.generate_migrations(
            optimization_plan=state["optimization_plan"],
            old_ddl_statements=state["ddl_statements"],
            new_ddl_statements=state["out_ddl_statements"],
        )
        return state

    async def _optimize_queries(self, state: State) -> State:
        logger.info(f"[5/6] Optimizing {len(state['queries'])} queries in parallel...")

        async def _process(q: dict[str, Any]) -> dict[str, str]:
            optimized = await self.query_agent.optimize_query(
                query=q["query"],
                migration_commands=state["out_migrations"],
            )
            return {"queryid": q["queryid"], "query": optimized}

        state["out_queries"] = await asyncio.gather(
            *[_process(q) for q in state["queries"]]
        )
        logger.info(f"[5/6] Optimized {len(state['out_queries'])} queries")
        return state

    def _form_output(self, state: State) -> dict:
        logger.info("[6/6] Forming final output")
        return {
            "out_ddl_statements": state["out_ddl_statements"],
            "out_migrations": state["out_migrations"],
            "out_queries": state["out_queries"],
        }

    async def run(self, data: dict) -> dict:
        logger.info("Starting optimization pipeline")

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
        result = final_state.get("form_output", final_state)

        logger.info("Pipeline complete")
        return result
