from dishka import Provider, Scope, make_async_container, provide

from src.agents.pipeline.orchestrator import PipelineOptimizer
from src.services.task_manager import TaskManager
from src.settings import AppSettings, settings


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_settings(self) -> AppSettings:
        return settings

    @provide(scope=Scope.APP)
    async def provide_task_manager(self, s: AppSettings) -> TaskManager:
        return TaskManager(
            ttl=s.task_ttl_seconds,
            cleanup_interval=s.task_cleanup_interval_seconds,
        )

    @provide(scope=Scope.APP)
    async def provide_optimizer(self, s: AppSettings) -> PipelineOptimizer:
        return PipelineOptimizer(s)


di_container = make_async_container(AppProvider())
