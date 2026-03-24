from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.agents.prompts.analyst import ANALYZE_SCHEMA


class AnalystAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def analyze(
        self,
        ddl_statements: list[str],
        queries: list[dict],
    ) -> str:
        logger.info("Starting schema and query analysis...")

        ddl_text = "\n".join(ddl_statements)
        queries_block = "\n\n".join(
            f"Query #{i + 1} (Impact: {q.get('runquantity', 0)} runs x {q.get('executiontime', 0)}s)\n"
            f"ID: {q.get('queryid')}\n"
            f"SQL:\n{q.get('query')}"
            for i, q in enumerate(queries[:10])
        )

        prompt_text = ANALYZE_SCHEMA.format(
            ddl_statements=ddl_text,
            queries=queries_block,
        )

        result = await self.llm.ainvoke(prompt_text)
        plan = result.content

        logger.info(f"Analysis complete. Plan length: {len(plan)} chars")
        return plan
