import json
import sys
import time

import requests
import trino

# --- Конфиг FastAPI ---
NEW_URL = "http://localhost:8000/tasks/new"
STATUS_URL = "http://localhost:8000/tasks/status"
GETRESULT_URL = "http://localhost:8000/tasks/getresult"

# "url": "jdbc:trino://trino.czxqx2r9.data.bizmrg.com:443?user=hackuser&password=dovq(ozaq8ngt)oS",

# --- Конфиг Trino ---
TRINO_HOST = "trino.czxqx2r9.data.bizmrg.com"  # или хост Trino
TRINO_PORT = 443
TRINO_USER = "hackuser"
TRINO_PASSWORD = "dovq(ozaq8ngt)oS"

with open("test.json") as file:
    results = json.load(file)

# --- Подключение к Trino ---
conn = trino.dbapi.connect(
    host=TRINO_HOST,
    port=TRINO_PORT,
    user=TRINO_USER,
    http_scheme="https" if TRINO_PORT == 443 else "http",
    auth=trino.auth.BasicAuthentication(TRINO_USER, TRINO_PASSWORD),
)
cursor = conn.cursor()

try:
    cursor.execute("drop schema iceberg.optimized cascade")
    cursor.execute("create schema iceberg.optimized")
except Exception as e:
    print(e)


# --- Выполняем все DDL и Queries ---
for item in results.get("ddl", []):
    statement = item["statement"]

    statement = statement.replace("flights.optimized", "iceberg.optimized")
    statement = statement.replace("quests.optimized", "iceberg.optimized")
    statement = statement.replace("quests.public", "iceberg.default")
    statement = statement.replace("flights.public", "iceberg.default")
    statement = statement.replace(";", "")

    print(f"Executing DDL: {statement}")
    cursor.execute(statement)

for item in results.get("migrations", []):
    statement = item["statement"]

    statement = statement.replace("flights.optimized", "iceberg.optimized")
    statement = statement.replace("quests.optimized", "iceberg.optimized")
    statement = statement.replace("quests.public", "iceberg.default")
    statement = statement.replace("flights.public", "iceberg.default")
    statement = statement.replace(";", "")

    print(f"Executing DDL: {statement}")
    cursor.execute(statement)

results_summary = []  # тут будем хранить (queryid, time)

for query_item in results.get("queries", []):
    query = query_item["query"]

    query = query.replace("flights.optimized", "iceberg.optimized")
    query = query.replace("quests.optimized", "iceberg.optimized")
    query = query.replace("quests.public", "iceberg.default")
    query = query.replace("flights.public", "iceberg.default")
    query = query.replace(";", "")

    print(f"Executing Query: {query}")

    start = time.perf_counter()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print("huihui:", e)
        rows = []
    end = time.perf_counter()

    elapsed = end - start
    results_summary.append((query_item["queryid"], elapsed))

    print(f"Result of QueryID {query_item['queryid']}: (took {elapsed:.4f}s)")
    for row in rows:
        print(row)
    print("-" * 40)

# финальная таблица
print("\nFinal summary (QueryID | Time in seconds)")
print("-" * 40)
for qid, t in results_summary:
    print(f"{qid:<10} | {t:.4f}")
