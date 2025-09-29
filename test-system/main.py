import json
import sys
import time

import requests
import trino

# --- Конфиг FastAPI ---
NEW_URL = "http://localhost:8000/mocks/new"
STATUS_URL = "http://localhost:8000/mocks/status"
GETRESULT_URL = "http://localhost:8000/mocks/getresult"

# --- Конфиг Trino ---
TRINO_HOST = "89.23.98.75"  # или хост Trino
TRINO_PORT = 8080
TRINO_USER = "user"

# --- Загружаем JSON задачу ---
with open("../data/flights.json", "r") as f:
    task_data = json.load(f)

# --- Отправляем задачу ---
resp = requests.post(NEW_URL, json=task_data)
resp.raise_for_status()
task_id = resp.json().get("taskid", "unknown")
print(f"Task created: {task_id}", file=sys.stderr)

# --- Ожидаем выполнения ---
while True:
    resp = requests.get(STATUS_URL, params={"taskid": task_id})
    resp.raise_for_status()
    status = resp.json().get("status", "")
    print(f"Status: {status}")
    if status == "DONE":
        break
    elif status == "FAILED":
        print("Task failed")
        sys.exit(1)
    time.sleep(1)

# --- Получаем результаты ---
resp = requests.get(GETRESULT_URL, params={"taskid": task_id})
resp.raise_for_status()
results = resp.json()

# --- Подключение к Trino ---
conn = trino.dbapi.connect(
    host=TRINO_HOST,
    port=TRINO_PORT,
    user=TRINO_USER,
    http_scheme="https" if TRINO_PORT == 443 else "http",
    auth=trino.auth.BasicAuthentication(TRINO_USER, ""),
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

for query_item in results.get("queries", []):
    query = query_item["query"]

    query = query.replace("flights.optimized", "iceberg.optimized")
    query = query.replace("quests.optimized", "iceberg.optimized")
    query = query.replace("quests.public", "iceberg.default")
    query = query.replace("flights.public", "iceberg.default")
    query = query.replace(";", "")

    print(f"Executing Query: {query}")
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"Result of QueryID {query_item['queryid']}:")
    for row in rows:
        print(row)
    print("-" * 40)
