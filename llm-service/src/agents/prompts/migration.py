DEVELOP_MIGRATIONS_FROM_PLAN = """
Role: Senior Database Migration Developer
Stack: Trino + Iceberg
DO NOT USE PARTITIONING.

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
- Filtering: Apply WHERE clauses to exclude invalid/archived data

TABLE SPLIT/MERGE HANDLING:
- Split (1 -> N): Use CASE statements or multiple INSERTs with WHERE
- Merge (N -> 1): Use UNION ALL with source identifier column
- Ensure FK relationships preserved via JOIN validation

ERROR HANDLING:
- Wrap type casts: TRY_CAST for nullable columns
- Handle NULLs: COALESCE(col, default_value)
- Validate constraints: Add WHERE clauses to filter invalid data

OUTPUT FORMAT:
- One SQL statement per line ending with semicolon
- No comments, no blank lines, no markdown
- Order: CREATE -> INSERT -> ALTER -> CREATE MV

BE SHORT AND CONCISE."""
