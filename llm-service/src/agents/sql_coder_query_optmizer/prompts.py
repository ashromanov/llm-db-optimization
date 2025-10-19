OPTIMIZE_QUERY = """
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
Rewrite the following Trino SQL query for optimal performance on Apache Iceberg tables.

KEY RULES:
1.  Output Format:
    - Respond ONLY with the final, optimized SQL statement.
    - Do NOT include any comments, explanations, markdown code fences, or extra text.

2.  Trino Dialect & Constraints:
    - Always use the full table path: catalog.schema.table.
    - Use standard double quotes for identifiers, e.g., "my_column".
    - Do NOT create or use Materialized Views.

3.  Optimization Techniques:
    - Pushdown WHERE filters to the source tables.
    - Reorder joins to filter data early (smaller or more selective tables first).
    - Simplify predicates (e.g., OR on the same column becomes IN (...)).
    - Use UNION ALL instead of UNION if duplicate removal is not needed.
    - Prefer EXISTS over IN for large, uncorrelated subqueries.
    - Avoid SELECT * if the DDL schema is provided; select only necessary columns.

Original Query:
```sql
{query}
```
DDL Statements for Context:
{ddls}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
