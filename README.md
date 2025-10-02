
# LLM SQL & DB optimizer ⚡️

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Сервис для автоматической оптимизации баз данных**

Используя языковые модели (LLM) и анализ метаданных Data Lakehouse (S3, Apache Iceberg, Trino, Spark), наш сервис формирует рекомендации по оптимизации хранения данных и SQL-запросов.

[Запуск решения](#запуск-решения) • [API Документация](#-документация-api) • [Технологии](#️-технологический-стек)

---

## 📊 Архитектура

```mermaid
flowchart TB
    Client[👤 Клиент] -->|HTTP Request| API[🌐 FastAPI Server]
    API --> TaskManager[📋 Task Manager]
    TaskManager --> Optimizer[🤖 LLM Optimizer Agent]
    Optimizer --> DDLAgent[📝 DDL Agent]
    Optimizer --> QueryAgent[🔍 Query Agent]
    Optimizer --> MigrationAgent[🔄 Migration Agent]

    DDLAgent --> Optimizer
    QueryAgent --> Optimizer
    MigrationAgent --> Optimizer

    Optimizer --> Results[✅ Results Storage]
    Results --> API
```


## Запуск решения:

1. Клонируйте репозиторий проекта:

```bash
git clone git@github.com:ashromanov/llm-db-optimization.git
cd llm-db-optimization/llm-service
```
2. Запустите сервис через Docker Compose:

```bash
docker compose up -d
```

3. После запуска сервис будет доступен по адресу:

```
http://localhost:8000
```

4. Swagger документация будет доступна по адресу:

```
http://localhost:8000/docs
```

## 📚 Документация API
### Эндпоинты для управления задачами

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `<endpoint>/new` | Создать задачу оптимизации |
| `GET` | `<endpoint>/status?<task_id>` | Получить статус задачи |
| `GET` | `<endpoint>/getresult?<task_id>` | Получить результат задачи |
#### 1. Создать задачу

**POST** `<endpoint>/new`
Создает новую задачу по оптимизации базы данных.

**Тело запроса:**

```json
{
  "url": "trino://user:pass@localhost:5432/mydb",
  "ddl": [
    {
      "statement": "CREATE TABLE T1 (id INT PRIMARY KEY, name VARCHAR(100));"
      }
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
  "taskid": "c8ed3309-1acb-439a-b32b-f802ba41db3e"
}
```

---

#### 2. Получить статус задачи

**GET** `<endpoint>/status?taskid={taskid}`
Проверяет статус созданной задачи.

**Параметры запроса:**

* `taskid` (строка, обязательный): ID целевой задачи

**Ответ:**

```json
{
  "status": "DONE | RUNNING | FAILED"
}
```

---

#### 3. Получить результат задачи

**GET** `<endpoint>/getresult?taskid={taskid}`
Возвращает результаты выполненной задачи.

**Параметры запроса:**

* `taskid` (строка, обязательный): ID целевой задачи

**Ответ:**

```json
{
  "ddl": [
    {
      "statement": "CREATE TABLE optimized_table (...)"
    }
  ],
  "migrations": [
    {
      "statement": "INSERT INTO optimized_table SELECT * FROM old_table"
    }
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

## 🛠️ Технологический стек

<table>
<tr>
<td align="center" width="33%">

### 🐍 Backend
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Dishka](https://img.shields.io/badge/Dishka-DI-purple?style=for-the-badge)

</td>
<td align="center" width="33%">

### 🤖 AI/ML
![LangGraph](https://img.shields.io/badge/LangGraph-Framework-FF6F00?style=for-the-badge)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?style=for-the-badge)
![GPT-OSS](https://img.shields.io/badge/GPT--OSS-20B-412991?style=for-the-badge&logo=openai&logoColor=white)

</td>
<td align="center" width="33%">

### 🐳 DevOps
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-Configured-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</td>
</tr>
</table>

---

### 📦 Полный список технологий

| Категория | Технология | Описание |
|-----------|-----------|----------|
| **🐍 Язык** | Python 3.13 | Современная версия Python с улучшенной производительностью |
| **🌐 Web Framework** | FastAPI | Высокопроизводительный асинхронный фреймворк |
| **💉 DI Container** | Dishka | Мощный контейнер для внедрения зависимостей |
| **🤖 LLM Framework** | LangGraph, LangChain | Фреймворки для работы с языковыми моделями |
| **🧠 AI Model** | [GPT-OSS 20B](https://huggingface.co/openai/gpt-oss-20b) | Языковая модель для анализа и оптимизации |
| **📖 Documentation** | OpenAPI / Swagger | Автоматическая интерактивная документация API |
| **🐳 Containerization** | Docker, Docker Compose | Контейнеризация и оркестрация сервисов |


## 📞 Контакты и поддержка

<div align="center">

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-red?style=for-the-badge&logo=github)](https://github.com/ashromanov/llm-db-optimization/issues)
[![GitHub Stars](https://img.shields.io/github/stars/ashromanov/llm-db-optimization?style=for-the-badge)](https://github.com/ashromanov/llm-db-optimization/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/ashromanov/llm-db-optimization?style=for-the-badge)](https://github.com/ashromanov/llm-db-optimization/network/members)  

[![Telegram](https://img.shields.io/badge/Telegram-Андрей-blue?style=for-the-badge&logo=telegram)](https://t.me/ShadowP1e)
[![Telegram](https://img.shields.io/badge/Telegram-Иван-blue?style=for-the-badge&logo=telegram)](https://t.me/iwance)
[![Telegram](https://img.shields.io/badge/Telegram-Асхат-blue?style=for-the-badge&logo=telegram)](https://t.me/Ashromanov)

</div>

