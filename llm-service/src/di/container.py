from dishka import Provider, Scope, make_async_container, provide

from src.services.task_manager import TaskManager


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_task_manager(self):
        return TaskManager()


di_container = make_async_container(AppProvider())
