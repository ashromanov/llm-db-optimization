from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from loguru import logger

from src.api.routes import tasks
from src.di.container import di_container

app = FastAPI()
app.include_router(tasks.router)

setup_dishka(container=di_container, app=app)
logger.add("app.log", rotation="10 MB", retention=1)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
