from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.agents.prompts.query import OPTIMIZE_QUERY
from src.agents.sql_utils import strip_markdown


class QueryAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def optimize_query(
        self,
        query: str,
        migration_commands: list[str],
    ) -> str:
        prompt_text = OPTIMIZE_QUERY.format(
            migration_commands="\n".join(migration_commands),
            query=query,
        )

        result = await self.llm.ainvoke(prompt_text)
        optimized = strip_markdown(result.content)

        logger.debug(f"Optimized query ({len(query)} -> {len(optimized)} chars)")
        return optimized
