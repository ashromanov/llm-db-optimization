from fastapi import FastAPI

from src.api.routes import tasks

app = FastAPI()
app.include_router(tasks.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
