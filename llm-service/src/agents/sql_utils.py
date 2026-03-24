import re
from urllib.parse import parse_qs, urlparse

import sqlglot
from loguru import logger
from sqlglot.optimizer import optimize


def strip_markdown(text: str) -> str:
    text = re.sub(r"^```[\w]*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text, flags=re.MULTILINE)
    text = text.replace("```", "")
    return text.strip()


def split_sql_statements(text: str) -> list[str]:
    cleaned = strip_markdown(text).replace("\n", " ")
    parts = [s.strip() for s in cleaned.split(";") if s.strip()]
    return [p + ";" for p in parts]


def parse_jdbc_url(jdbc_url: str) -> dict[str, str | None]:
    try:
        if jdbc_url.startswith("jdbc:"):
            jdbc_url = jdbc_url[5:]

        parsed = urlparse(jdbc_url)
        dialect = (parsed.scheme or "trino").lower()

        dialect_map = {
            "postgresql": "postgres",
            "mysql": "mysql",
            "trino": "trino",
            "presto": "presto",
            "hive": "hive",
            "snowflake": "snowflake",
            "bigquery": "bigquery",
        }
        dialect = dialect_map.get(dialect, dialect)

        path = parsed.path.lstrip("/")
        catalog, db = None, None
        if path:
            parts = path.split("/")
            catalog = parts[0] if len(parts) >= 1 else None
            db = parts[1] if len(parts) >= 2 else None

        params = parse_qs(parsed.query)
        if not catalog and "catalog" in params:
            catalog = params["catalog"][0]
        if not db and "schema" in params:
            db = params["schema"][0]

        return {
            "dialect": dialect,
            "db": db,
            "catalog": catalog,
            "host": parsed.hostname,
        }
    except Exception as e:
        logger.warning(f"Failed to parse JDBC URL: {e}")
        return {"dialect": "trino", "db": None, "catalog": None, "host": None}


def ddl_list_to_schema(ddls: list[str], dialect: str = "trino") -> dict:
    tables: dict[str, dict[str, str]] = {}
    for ddl in ddls:
        try:
            expr = sqlglot.parse_one(ddl, read=dialect)
            if not isinstance(expr, sqlglot.exp.Create):
                continue
            table_name = expr.this.name
            columns = {}
            for col in expr.find_all(sqlglot.exp.ColumnDef):
                kind = col.args.get("kind")
                columns[col.name] = str(kind.this).upper() if kind else "UNKNOWN"
            tables[table_name] = columns
        except Exception as e:
            logger.warning(f"Failed to parse DDL: {e}")
    return tables


def validate_sql(query: str, dialect: str = "trino") -> tuple[bool, str]:
    try:
        parsed = sqlglot.parse_one(query, read=dialect)
        if parsed is None:
            return False, "Failed to parse query"
        parsed.sql(dialect=dialect)
        return True, ""
    except Exception as e:
        return False, str(e)


def optimize_sql_with_sqlglot(
    query: str,
    schema: dict,
    dialect: str = "trino",
    db: str | None = None,
    catalog: str | None = None,
) -> tuple[str, bool]:
    try:
        is_valid, error = validate_sql(query, dialect)
        if not is_valid:
            logger.warning(f"Input query validation failed: {error}")
            return query, False

        parsed = sqlglot.parse_one(query, read=dialect)
        optimized = optimize(
            parsed, schema=schema, db=db, catalog=catalog, dialect=dialect
        )
        optimized_sql = optimized.sql(dialect=dialect).replace('"', "")

        is_valid, error = validate_sql(optimized_sql, dialect)
        if not is_valid:
            logger.warning(f"Optimized query validation failed: {error}")
            return query, False

        return optimized_sql, True
    except Exception as e:
        logger.error(f"SQL optimization failed: {e}")
        return query, False
