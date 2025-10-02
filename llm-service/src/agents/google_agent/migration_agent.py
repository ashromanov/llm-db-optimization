"""
Migration Agent - Generates migration SQL scripts from optimization plan.
Uses OpenRouter API for safe, idempotent migration generation.
"""

import re
from langchain_openai import ChatOpenAI

from .prompts_new import DEVELOP_MIGRATIONS_FROM_PLAN


class MigrationAgent:
    """
    Agent responsible for generating SQL migration scripts.
    Output: Safe, idempotent migration SQL statements.
    Model: OpenRouter API (precise migration logic)
    """
    
    MODEL_NAME = "openai/gpt-oss-20b"
    
    def __init__(self, openrouter_api_key: str, temperature: float = 0.0):
        """
        Initialize Migration Agent.
        
        Args:
            openrouter_api_key: OpenRouter API key.
            temperature: Sampling temperature (0.0 for deterministic SQL generation).
        """
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
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
    
    def _split_clean(self, text: str) -> list[str]:
        """
        Split SQL statements by lines.
        
        Args:
            text: Raw SQL text.
        
        Returns:
            list[str]: List of SQL statements (one per line).
        """
        cleaned = self._strip_markdown_and_clean(text)
        # Split by newlines and keep non-empty lines
        return [line.strip() for line in cleaned.split("\n") if line.strip()]
    
    async def generate_migrations(
        self,
        optimization_plan: str,
        old_ddl_statements: list[str],
        new_ddl_statements: list[str],
    ) -> list[str]:
        """
        Generate migration SQL statements based on optimization plan.
        
        Args:
            optimization_plan: Natural language plan from AnalystAgent.
            old_ddl_statements: Original DDL statements.
            new_ddl_statements: New optimized DDL statements.
        
        Returns:
            list[str]: Migration SQL statements (Trino compatible).
        """
        print("[MigrationAgent] Generating migration statements...")
        
        # Format inputs
        old_ddl_text = "\n".join(old_ddl_statements)
        new_ddl_text = "\n".join(new_ddl_statements)
        
        # Build prompt
        prompt_text = DEVELOP_MIGRATIONS_FROM_PLAN.format(
            optimization_plan=optimization_plan,
            input_ddl_statements=old_ddl_text,
            output_ddl_statements=new_ddl_text,
        )
        
        # Invoke LLM
        result = await self.llm.ainvoke(prompt_text)
        
        # Clean and split
        migration_statements = self._split_clean(result.content)
        
        print(f"[MigrationAgent] ✓ Generated {len(migration_statements)} migration statements")
        
        return migration_statements
