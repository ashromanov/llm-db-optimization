"""
Developer Agent - Generates SQL DDL from optimization plan.
Uses Gemini 2.5 Pro for precise DDL generation.
"""

import re
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts_new import DEVELOP_DDL_FROM_PLAN


class DeveloperAgent:
    """
    Agent responsible for generating optimized DDL based on optimization plan.
    Output: SQL DDL statements only (migrations handled by MigrationAgent).
    Model: Gemini 2.5 Pro (code generation with reasoning)
    """
    
    MODEL_NAME = "gemini-2.5-flash"
    
    def __init__(self, google_api_key: str, temperature: float = 0.0):
        """
        Initialize Developer Agent.
        
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
    
    async def develop_ddl(
        self,
        optimization_plan: str,
        original_ddl_statements: list[str],
    ) -> list[str]:
        """
        Generate optimized DDL statements based on optimization plan.
        
        Args:
            optimization_plan: Natural language plan from AnalystAgent.
            original_ddl_statements: Original DDL statements.
        
        Returns:
            list[str]: New optimized DDL statements.
        """
        print("[DeveloperAgent] Generating optimized DDL statements...")
        
        # Format inputs
        ddl_text = "\n".join(original_ddl_statements)
        
        # Build prompt
        prompt_text = DEVELOP_DDL_FROM_PLAN.format(
            optimization_plan=optimization_plan,
            input_ddl_statements=ddl_text,
        )
        
        # Invoke LLM
        result = await self.llm.ainvoke(prompt_text)
        
        # Clean and split
        new_ddl_statements = self._split_clean(result.content)
        
        print(f"[DeveloperAgent] ✓ Generated {len(new_ddl_statements)} DDL statements")
        
        return new_ddl_statements
