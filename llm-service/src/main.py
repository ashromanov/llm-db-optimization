from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from loguru import logger

from src.api.routes import health, tasks
from src.di.container import di_container
from src.services.task_manager import TaskManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI SQL Optimizer")
    task_manager = await di_container.get(TaskManager)
    await task_manager.start_cleanup_loop()
    yield
    await task_manager.stop_cleanup_loop()
    logger.info("Shutting down")


app = FastAPI(
    title="AI SQL Optimizer",
    version="0.1.0",
    description="LLM-powered SQL & database optimization service",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(tasks.router)

setup_dishka(container=di_container, app=app)
