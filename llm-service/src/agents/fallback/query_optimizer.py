import asyncio
import re
from typing import Any

from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.agents.prompts.query import OPTIMIZE_QUERY_FALLBACK
from src.agents.sql_utils import (
    ddl_list_to_schema,
    optimize_sql_with_sqlglot,
    parse_jdbc_url,
)


class FallbackQueryOptimizer:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.dialect = "trino"
        self.db: str | None = None
        self.catalog: str | None = None

    @staticmethod
    def _clean_llm_output(text: str) -> str:
        text = re.sub(r"```(?:\w+)?", "", text)
        text = re.sub(r"--[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and not text.endswith(";"):
            text += ";"
        return text

    async def _process_single_query(
        self,
        query_data: dict[str, Any],
        ddls: list[str],
    ) -> dict[str, str]:
        query_id = query_data["queryid"]
        original_query = query_data["query"]
        schema = ddl_list_to_schema(ddls, dialect=self.dialect)
        ddls_text = "\n".join(ddls)

        # Tier 1: LLM optimization + SQLGlot validation
        try:
            prompt = OPTIMIZE_QUERY_FALLBACK.format(
                query=original_query,
                ddls=ddls_text,
                dialect=self.dialect,
            )
            result = await self.llm.ainvoke(prompt)
            cleaned = self._clean_llm_output(result.content)

            optimized, success = optimize_sql_with_sqlglot(
                cleaned,
                schema,
                self.dialect,
                self.db,
                self.catalog,
            )
            if success:
                logger.info(f"Query {query_id}: optimized via LLM")
                return {"queryid": str(query_id), "query": optimized}

            logger.warning(f"Query {query_id}: LLM output invalid, trying fallback")
        except Exception as e:
            logger.warning(f"Query {query_id}: LLM failed: {e}")

        # Tier 2: SQLGlot-only optimization
        try:
            optimized, success = optimize_sql_with_sqlglot(
                original_query,
                schema,
                self.dialect,
                self.db,
                self.catalog,
            )
            if success:
                logger.info(f"Query {query_id}: optimized via SQLGlot only")
                return {"queryid": str(query_id), "query": optimized}
        except Exception as e:
            logger.warning(f"Query {query_id}: SQLGlot fallback failed: {e}")

        # Tier 3: Return original
        logger.info(f"Query {query_id}: returning original unchanged")
        return {"queryid": str(query_id), "query": original_query}

    async def run(self, data: dict[str, Any]) -> dict[str, Any]:
        metadata = data.get("metadata", {})

        if isinstance(metadata, dict) and "url" in metadata:
            jdbc_config = parse_jdbc_url(metadata["url"])
            self.dialect = jdbc_config["dialect"]
            self.db = jdbc_config["db"]
            self.catalog = jdbc_config["catalog"]

        logger.info(f"FallbackQueryOptimizer: dialect={self.dialect}")

        tasks = [
            self._process_single_query(q, data["ddl_statements"])
            for q in data["queries"]
        ]
        optimized_queries = await asyncio.gather(*tasks)

        return {
            "out_ddl_statements": [],
            "out_migrations": [],
            "out_queries": optimized_queries,
        }
