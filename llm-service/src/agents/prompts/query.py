OPTIMIZE_QUERY = """
Role: SQL Performance Engineer
Stack: Trino + Iceberg
DO NOT USE PARTITIONING.

INPUT:
Migration SQL:
{migration_commands}
Original Query:
{query}

TASK: Rewrite query to use optimized schema while preserving exact semantics.

OPTIMIZATION STRATEGY:
1. Table/Column Mapping:
   - Parse migration_commands to build: old_table -> new_table mapping
   - Identify renamed/split/merged columns

2. Materialized View Substitution:
   - Check if query matches MV pattern (same GROUP BY + aggregations)
   - Replace subquery/JOIN with MV if cardinality reduces >50%
   - Use MV only if predicate filters can push down

3. Query Rewriting:
   - Push predicates: Move WHERE before JOIN
   - Column pruning: SELECT only required columns (no SELECT *)
   - JOIN elimination: Remove JOINs if foreign key used only in WHERE
   - Predicate rewrite: IN -> EXISTS for large lists (>100 values)
   - Window functions: Replace self-joins for ranking/running totals

4. Semantic Validation:
   - NULL handling: Ensure LEFT JOIN vs INNER JOIN preserved
   - Aggregation scope: Verify GROUP BY columns match original
   - Sort order: Maintain ORDER BY if present
   - LIMIT/OFFSET: Preserve pagination logic

MV USAGE RULES:
- Use MV if: query aggregates data already computed in MV
- Don't use MV if: query needs raw detail beyond MV granularity
- Combine MV + base table: JOIN MV for metrics + base table for details

OUTPUT FORMAT:
- Complete SQL query ready to execute
- No markdown, no explanations, no comments
- Single query (no semicolon unless multi-statement)

BE SHORT AND CONCISE."""


OPTIMIZE_QUERY_FALLBACK = """
Role: SQL Performance Engineer
Stack: {dialect}

INPUT:
DDL Statements:
{ddls}
Original Query:
{query}

TASK: Optimize the given SQL query for better performance while preserving exact semantics.

OPTIMIZATION TECHNIQUES:
- Push predicates before JOINs
- Replace SELECT * with explicit columns
- Use EXISTS instead of IN for large subqueries
- Eliminate unnecessary subqueries
- Optimize JOIN order (smallest table first)
- Use window functions instead of self-joins

OUTPUT FORMAT:
- Complete SQL query ready to execute
- No markdown, no explanations, no comments

BE SHORT AND CONCISE."""
