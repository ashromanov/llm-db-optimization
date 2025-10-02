# LLM оптимизация баз данных

Интеллектуальный сервис, который с помощью языковых моделей (LLM) и анализа метаданных Data Lakehouse (S3, Apache Iceberg, Trino, Spark) формирует рекомендации по оптимизации хранения данных и SQL-запросов.

## Архитектура

ВОТ СЮДА ПОТОМ ВСТАВЛЯТЬ ПРИКОЛЫ ИИШНЫЕ

## Быстрый старт

Для быстрого запуска сервиса рекомендуется использовать Docker Compose. Это создаст все необходимые контейнеры и зависимости автоматически.

### Шаги:

1. Клонируйте репозиторий проекта:

```bash
git clone git@github.com:ashromanov/llm-db-optimization.git
cd llm-db-optimization/llm-service
```
2. Запустите сервис через Docker Compose:

```bash
docker-compose up -d
```

3. После запуска сервис будет доступен по адресу:

```
http://localhost:8000
```

4. Swagger документация будет достна по адресу:

```
http://localhost:8000/docs
```

## Документация API

Сервис предоставляет эндпоинты для создания, отслеживания и получения результатов задач по оптимизации базы данных. API использует REST и возвращает ответы в формате JSON.

### Эндпоинты для задач (Tasks)

#### 1. Создать задачу

**POST** `/tasks/new`
Создает новую задачу по оптимизации базы данных.

**Тело запроса:**

```json
{
  "url": "trino://user:pass@localhost:5432/mydb",
  "ddl": [
    {"statement": "CREATE TABLE Table1 (id INT PRIMARY KEY, name VARCHAR(100));"}
  ],
  "queries": [
    {
      "queryid": "uuid",
      "query": "SELECT * FROM Table1",
      "runquantity": 10,
      "executiontime": 5
    }
  ]
}
```

**Ответ:**

```json
{
  "taskid": "уникальный-id-задачи"
}
```

---

#### 2. Получить статус задачи

**GET** `/tasks/status?taskid={taskid}`
Проверяет статус созданной задачи.

**Параметры запроса:**

* `taskid` (строка, обязательный): ID целевой задачи

**Ответ:**

```json
{
  "status": "pending | running | completed | failed"
}
```

---

#### 3. Получить результат задачи

**GET** `/tasks/getresult?taskid={taskid}`
Возвращает результаты выполненной задачи.

**Параметры запроса:**

* `taskid` (строка, обязательный): ID целевой задачи

**Ответ:**

```json
{
  "ddl": [
    {"statement": "CREATE TABLE optimized_table (...)"}
  ],
  "migrations": [
    {"statement": "INSERT INTO optimized_table SELECT * FROM old_table"}
  ],
  "queries": [
    {
      "queryid": "uuid",
      "query": "WITH MonthlyFlightCounts AS (...) SELECT ..."
    }
  ]
}
```

---

## Технологический стек

- **Python 3.13**
- **Веб-фреймворк:** FastAPI
- **Внедрения зависимостей:** Dishka
- **LLM фреймворки:** LangGraph, LangChain
- **Модели ИИ:** GPT-OSS 20B (https://huggingface.co/openai/gpt-oss-20b)
- **Документация:** OpenAPI / Swagger
- **Контейнеризация:** Docker, Docker Compose
