DEVELOP_DDL_FROM_PLAN = """
Role: Senior Database Migration Developer
Stack: Trino + Iceberg
DO NOT USE PARTITIONING.

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

TASK: Generate DDL statements for optimized schema.

MANDATORY RULES:
1. Paths: Always use full 3-part names (<catalog>.<schema>.<table>)
2. Order: CREATE SCHEMA -> CREATE TABLE (dependency order) -> CREATE MATERIALIZED VIEW
3. Formats: Only ORC, PARQUET, or AVRO (must match optimization plan)
4. Types: Use Trino types (BIGINT, VARCHAR, DOUBLE, TIMESTAMP(6), DATE, BOOLEAN, ARRAY, MAP, ROW)
5. Constraints: Preserve NOT NULL from source schema
6. MVs: Must reference only tables in same schema, use aggregate functions only

DATA TYPE MIGRATION:
- Integer-like strings -> BIGINT
- High-cardinality VARCHAR -> VARCHAR (no length limit)
- Timestamps -> TIMESTAMP(6) WITH TIME ZONE
- JSON columns -> ROW or MAP types where possible

MV DESIGN PATTERNS:
- Pre-aggregated metrics: SUM, COUNT, AVG with GROUP BY
- Denormalized joins: Frequently joined tables
- Filtered subsets: WHERE clauses for common predicates

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

BE SHORT AND CONCISE."""
