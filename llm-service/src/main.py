from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.api.routes import mocks, tasks
from src.di.container import di_container

app = FastAPI()
app.include_router(tasks.router)
app.include_router(mocks.router)

setup_dishka(container=di_container, app=app)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
