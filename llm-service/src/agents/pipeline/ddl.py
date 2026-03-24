from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.agents.prompts.ddl import DEVELOP_DDL_FROM_PLAN
from src.agents.sql_utils import split_sql_statements


class DDLAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def develop_ddl(
        self,
        optimization_plan: str,
        original_ddl_statements: list[str],
    ) -> list[str]:
        logger.info("Generating optimized DDL statements...")

        prompt_text = DEVELOP_DDL_FROM_PLAN.format(
            optimization_plan=optimization_plan,
            ddl_statements="\n".join(original_ddl_statements),
        )

        result = await self.llm.ainvoke(prompt_text)
        statements = split_sql_statements(result.content)

        logger.info(f"Generated {len(statements)} DDL statements")
        return statements
