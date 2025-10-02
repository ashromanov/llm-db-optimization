ANALYZE_SCHEMA = """
!!!BE SHORT AND CONCISE IN YOUR ANSWER, OUTPUT AS LITTLE TEXT AS POSSIBLE!!!
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
   - Calculate: query frequency × data volume = optimization priority

3. Optimization Opportunities:
   - Type optimization: e.g., VARCHAR(255) → BIGINT for IDs
   - Denormalization candidates: tables joined in >30p of queries
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

Keep output under 4000 tokens. Prioritize high-impact optimizations."""


DEVELOP_DDL_FROM_PLAN = """
!!!BE SHORT AND CONCISE IN YOUR ANSWER, OUTPUT AS LITTLE TEXT AS POSSIBLE!!!
Role: Senior Database Migration Developer
Stack: Trino + Iceberg

SYNTAX REFERENCE:
CREATE SCHEMA [IF NOT EXISTS] <catalog>.<schema>;
CREATE TABLE <catalog>.<schema>.<table> (
  col1 TYPE [NOT NULL],
  col2 TYPE [DEFAULT value]
) WITH (format = '<FORMAT>');
CREATE MATERIALIZED VIEW <catalog>.<schema>.<mv>
WITH (format = '<FORMAT>')
AS <SELECT_QUERY>;

INPUT:
Optimization Plan:
{optimization_plan}
Source DDL:
{ddl_statements}
Query Workload:
{queries}

TASK: Generate DDL statements for optimized schema.

MANDATORY RULES:
1. Paths: Always use full 3-part names (<catalog>.<schema>.<table>)
2. Order: CREATE SCHEMA → CREATE TABLE (dependency order) → CREATE MATERIALIZED VIEW
3. Formats: Only ORC, PARQUET, or AVRO (must match optimization plan)
4. Types: Use Trino types (BIGINT, VARCHAR, DOUBLE, TIMESTAMP(6), DATE, BOOLEAN, ARRAY, MAP, ROW)
5. Constraints: Preserve NOT NULL from source schema
6. MVs: Must reference only tables in same schema, use aggregate functions only

DATA TYPE MIGRATION:
- Integer-like strings → BIGINT
- High-cardinality VARCHAR → VARCHAR (no length limit)
- Timestamps → TIMESTAMP(6) WITH TIME ZONE
- JSON columns → ROW or MAP types where possible

MV DESIGN PATTERNS:
- Pre-aggregated metrics: SUM, COUNT, AVG with GROUP BY
- Denormalized joins: Frequently joined tables
- Filtered subsets: WHERE clauses for common predicates

ERROR PREVENTION:
- Check MV query references only tables created earlier in script
- Validate aggregation functions are deterministic
- Ensure format is consistent within same schema

OUTPUT FORMAT:
- One SQL statement per line ending with semicolon
- No comments, no blank lines, no markdown
- Start with: CREATE SCHEMA IF NOT EXISTS <catalog>.<newschema>;

VALIDATION CHECKLIST (verify before output):
- Schema created before any tables
- Tables created before dependent MVs
- All table references use 3-part names
- All formats are ORC/PARQUET/AVRO
- MVs contain only SELECT queries

ERROR HANDLING:
- If constraints are contradictory, output: ERROR: [description]
- If input is ambiguous, state assumptions in format: ASSUMPTION: [statement]"""


DEVELOP_MIGRATIONS_FROM_PLAN = """
!!!BE SHORT AND CONCISE IN YOUR ANSWER, OUTPUT AS LITTLE TEXT AS POSSIBLE!!!
Role: Senior Database Migration Developer
Stack: Trino + Iceberg

SYNTAX REFERENCE:
CREATE TABLE IF NOT EXISTS... WITH (format = '...');
INSERT INTO target SELECT ... FROM source;
ALTER TABLE... ADD COLUMN... <TYPE> [DEFAULT <value>];
CREATE MATERIALIZED VIEW... WITH (format = '...')
AS SELECT...;

INPUT:
Optimization Plan:
{optimization_plan}
Source DDL:
{input_ddl_statements}
Target DDL:
{output_ddl_statements}

TASK: Generate idempotent migration statements to populate optimized schema.

MIGRATION PHASES:
1. CREATE TABLES (with IF NOT EXISTS)
2. MIGRATE DATA (with INSERT INTO... SELECT)
3. ALTER TABLES (add computed/derived columns)
4. CREATE MATERIALIZED VIEWS (after base data is loaded)

IDEMPOTENCY REQUIREMENTS:
- Tables: Use IF NOT EXISTS (safe to re-run)
- Data: Use INSERT INTO (Iceberg handles duplicates via snapshots)
- MVs: Use CREATE OR REPLACE (auto-refresh handles staleness)

DATA TRANSFORMATION PATTERNS:
- Type casting: CAST(old_col AS new_type)
- Column splitting: Parse VARCHAR into structured ROW
- Column merging: Concatenate or compute new columns
- Deduplication: Use ROW_NUMBER() OVER (PARTITION BY key ORDER BY timestamp DESC) WHERE rn = 1
- Filtering: Apply WHERE clauses to exclude invalid/archived data

TABLE SPLIT/MERGE HANDLING:
- Split (1 → N): Use CASE statements or multiple INSERTs with WHERE
- Merge (N → 1): Use UNION ALL with source identifier column
- Ensure FK relationships preserved via JOIN validation

ERROR HANDLING:
- Wrap type casts: TRY_CAST for nullable columns
- Handle NULLs: COALESCE(col, default_value)
- Validate constraints: Add WHERE clauses to filter invalid data

OUTPUT FORMAT:
- One SQL statement per line ending with semicolon
- No comments, no blank lines, no markdown
- Order: CREATE → INSERT → ALTER → CREATE MV

EXAMPLE (Split):
CREATE TABLE IF NOT EXISTS cat.new.orders_active (id BIGINT, status VARCHAR) WITH (format = 'PARQUET');
CREATE TABLE IF NOT EXISTS cat.new.orders_archived (id BIGINT, status VARCHAR) WITH (format = 'PARQUET');
INSERT INTO cat.new.orders_active SELECT id, status FROM cat.old.orders WHERE archived = false;
INSERT INTO cat.new.orders_archived SELECT id, status FROM cat.old.orders WHERE archived = true;

EXAMPLE (Merge with deduplication):
CREATE TABLE IF NOT EXISTS cat.new.users (id BIGINT, email VARCHAR, source VARCHAR) WITH (format = 'PARQUET');
INSERT INTO cat.new.users 
SELECT id, email, 'crm' as source FROM cat.old.crm_users
UNION ALL
SELECT id, email, 'web' as source FROM cat.old.web_users;

ERROR HANDLING:
- If constraints are contradictory, output: ERROR: [description]
- If input is ambiguous, state assumptions in format: ASSUMPTION: [statement]"""


OPTIMIZE_QUERY = """
!!!BE SHORT AND CONCISE IN YOUR ANSWER, OUTPUT AS LITTLE TEXT AS POSSIBLE!!!
Role: SQL Performance Engineer
Stack: Trino + Iceberg

INPUT:
Migration SQL:
{migration_commands}
Original Query:
{query}

TASK: Rewrite query to use optimized schema while preserving exact semantics.

OPTIMIZATION STRATEGY:
1. Table/Column Mapping:
   - Parse migration_commands to build: old_table → new_table mapping
   - Identify renamed/split/merged columns
   
2. Materialized View Substitution:
   - Check if query matches MV pattern (same GROUP BY + aggregations)
   - Replace subquery/JOIN with MV if cardinality reduces >50%
   - Use MV only if predicate filters can push down

3. Query Rewriting:
   - Push predicates: Move WHERE before JOIN
   - Column pruning: SELECT only required columns (no SELECT *)
   - JOIN elimination: Remove JOINs if foreign key used only in WHERE
   - Predicate rewrite: IN → EXISTS for large lists (>100 values)
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

ANTI-PATTERNS TO AVOID:
- Don't use MV for: INSERT, UPDATE, DELETE (read-only)
- Don't add WHERE filters not in original query
- Don't change aggregation functions (SUM → COUNT)
- Don't remove columns used in outer query

OUTPUT FORMAT:
- Complete SQL query ready to execute
- No markdown, no explanations, no comments
- Single query (no semicolon unless multi-statement)

VALIDATION (before output):
- All table references updated to new schema
- Column names match target DDL
- Aggregations match original semantics
- JOIN types preserved (INNER/LEFT/RIGHT)
- Result set cardinality unchanged

EXAMPLE:
SELECT u.name, m.order_count 
FROM new.users_opt u 
JOIN new.mv_user_order_stats m ON u.id = m.user_id;

ERROR HANDLING:
- If query cannot be optimized without changing semantics, output: WARNING: [reason] followed by updated table/column references only
- If migration_commands don't contain table mappings, output: ERROR: Cannot map tables from migration commands"""
