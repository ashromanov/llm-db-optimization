"""
Query Agent - Rewrites queries for optimized schema.
"""

import re

from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import OPTIMIZE_QUERY


class QueryAgent:
    """
    Agent responsible for rewriting queries to work with new schema.
    Output: Optimized SQL queries.
    Model: Gemini 2.5 Flash (fast, cost-effective for repetitive tasks)
    """

    MODEL_NAME = "gemini-2.5-flash-lite"

    def __init__(self, google_api_key: str, temperature: float = 0.0):
        """
        Initialize Query Optimizer Agent.

        Args:
            google_api_key: Google API key for Gemini.
            temperature: Sampling temperature (0.0 for deterministic SQL generation).
        """
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=self.MODEL_NAME,
            temperature=temperature,
        )

    def _strip_markdown_and_clean(self, text: str) -> str:
        """
        Remove markdown code blocks from LLM output.

        Args:
            text: Raw LLM output.

        Returns:
            str: Cleaned text with markdown blocks removed.
        """
        # Remove markdown code blocks
        text = re.sub(r"^```[\w]*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n```$", "", text, flags=re.MULTILINE)
        text = text.replace("```", "")

        return text.strip()

    async def optimize_query(
        self,
        query: str,
        migration_commands: list[str],
    ) -> str:
        """
        Optimize a single query based on migration commands.

        Args:
            query: Original SQL query.
            migration_commands: Migration SQL statements (hints about new schema).

        Returns:
            str: Optimized SQL query.
        """
        # Format inputs
        migration_text = "\n".join(migration_commands)

        # Build prompt
        prompt_text = OPTIMIZE_QUERY.format(
            migration_commands=migration_text,
            query=query,
        )

        # Invoke LLM
        result = await self.llm.ainvoke(prompt_text)

        # Clean output
        optimized_query = self._strip_markdown_and_clean(result.content)

        return optimized_query
