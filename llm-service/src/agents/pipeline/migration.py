from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.agents.prompts.migration import DEVELOP_MIGRATIONS_FROM_PLAN
from src.agents.sql_utils import split_sql_statements


class MigrationAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_migrations(
        self,
        optimization_plan: str,
        old_ddl_statements: list[str],
        new_ddl_statements: list[str],
    ) -> list[str]:
        logger.info("Generating migration statements...")

        prompt_text = DEVELOP_MIGRATIONS_FROM_PLAN.format(
            optimization_plan=optimization_plan,
            input_ddl_statements="\n".join(old_ddl_statements),
            output_ddl_statements="\n".join(new_ddl_statements),
        )

        result = await self.llm.ainvoke(prompt_text)
        statements = split_sql_statements(result.content)

        logger.info(f"Generated {len(statements)} migration statements")
        return statements
