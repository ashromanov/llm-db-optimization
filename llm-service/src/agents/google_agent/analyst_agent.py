"""
Analyst Agent - Analyzes database schema and queries to create optimization plan.
Uses OpenRouter API for deep analytical thinking.
"""

from langchain_openai import ChatOpenAI

from .prompts_new import ANALYZE_SCHEMA


class AnalystAgent:
    """
    Agent responsible for analyzing database schema and query patterns.
    Output: Natural language optimization plan (NO SQL code).
    Model: OpenRouter API (analytical reasoning)
    """
    
    MODEL_NAME = "openai/gpt-oss-20b"
    
    def __init__(self, openrouter_api_key: str, temperature: float = 0.1):
        """
        Initialize Analyst Agent.
        
        Args:
            openrouter_api_key: OpenRouter API key.
            temperature: Sampling temperature (0.1 for analytical consistency).
        """
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            model=self.MODEL_NAME,
            temperature=temperature,
        )
    
    async def analyze(
        self,
        ddl_statements: list[str],
        queries: list[dict],
    ) -> str:
        """
        Analyze database schema and queries to create optimization plan.
        
        Args:
            ddl_statements: List of DDL statements describing current schema.
            queries: List of queries with metrics (queryid, query, runquantity, executiontime).
                     Should be pre-sorted by impact (runquantity × executiontime).
        
        Returns:
            str: Natural language optimization plan with sections:
                 - Schema Analysis
                 - Query Patterns
                 - Optimization Plan
                 - Migration Strategy
        """
        print("[AnalystAgent] Starting schema and query analysis...")
        
        # Format inputs
        ddl_text = "\n".join(ddl_statements)
        queries_block = "\n\n".join([
            (
                f"Query #{i+1} (Impact: {q.get('runquantity', 0)} runs × {q.get('executiontime', 0)}ms)\n"
                f"ID: {q.get('queryid')}\n"
                f"SQL:\n{q.get('query')}"
            )
            for i, q in enumerate(queries[:10])  # Top 10 queries
        ])
        
        # Build prompt
        prompt_text = ANALYZE_SCHEMA.format(
            input_ddl_statements=ddl_text,
            input_queries=queries_block,
        )
        
        # Invoke LLM
        result = await self.llm.ainvoke(prompt_text)
        optimization_plan = result.content
        
        print("[AnalystAgent] ✓ Analysis complete. Plan generated.")
        print(f"[AnalystAgent] Plan length: {len(optimization_plan)} characters")
        
        return optimization_plan
