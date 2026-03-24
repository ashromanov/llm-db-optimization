ANALYZE_SCHEMA = """
Role: Senior Database Performance Analyst
Stack: Trino (distributed SQL) + Apache Iceberg (ACID transactions, schema evolution)

INPUT:
DDL Statements:
{ddl_statements}
Query Workload:
{queries}

TASK: Analyze schema and queries to create a detailed optimization plan.

ANALYSIS FRAMEWORK:
1. Schema Review:
   - Identify: table relationships, data types, column cardinality
   - Flag: wide tables (>50 cols), inefficient types (VARCHAR for numeric IDs), missing constraints

2. Query Pattern Analysis:
   - Categorize queries: OLTP (point lookups) vs OLAP (aggregations)
   - Identify: repeated JOINs, subqueries, common filters, aggregation patterns
   - Calculate: query frequency x data volume = optimization priority

3. Optimization Opportunities:
   - Type optimization: e.g., VARCHAR(255) -> BIGINT for IDs
   - Denormalization candidates: tables joined in >30% of queries
   - Materialized view candidates: aggregations computed in >3 queries
   - Column pruning: identify unused columns

4. Migration Blueprint:
   - Dependency graph: which tables must be created first
   - Data transformation logic: type casts, column merges, computed columns
   - MV refresh strategy: full rebuild vs incremental

CONSTRAINTS:
- No partitioning/indexing recommendations (Iceberg handles via metadata)
- Source tables are read-only (must create new tables)
- MVs are read-only (for SELECT only, not INSERT/UPDATE/DELETE)

OUTPUT FORMAT (strict structure):
## Schema Analysis
[For each table: row count estimate, column analysis, relationship diagram]

## Query Patterns
[For each pattern: frequency, cost estimate, bottleneck identification]

## Optimization Plan
[Prioritized list with: action, rationale, expected impact]

## Migration Strategy
[Ordered steps with: dependencies, transformation SQL patterns, rollback considerations]

ERROR HANDLING:
- If constraints are contradictory, output: ERROR: [description]
- If input is ambiguous, state assumptions in format: ASSUMPTION: [statement]

BE SHORT AND CONCISE. Keep output under 4000 tokens. Prioritize high-impact optimizations."""
