"""FastAPI lifespan integration for django-autowired."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Generic, TypeVar

from django_autowired import container
from django_autowired.backends.base import BackendName

T = TypeVar("T")


@asynccontextmanager
async def autowired_lifespan(
    app: Any,
    packages: list[str],
    backend: BackendName | str = "injector",
    extra_modules: list[Any] | None = None,
    exclude_patterns: set[str] | None = None,
) -> AsyncIterator[None]:
    """Async context manager for FastAPI lifespan that initializes the container.

    Usage::

        from functools import partial

        app = FastAPI(
            lifespan=partial(
                autowired_lifespan,
                packages=["myapp.services"],
            )
        )

    Args:
        app: The FastAPI application instance.
        packages: Package paths to scan.
        backend: Backend name.
        extra_modules: Backend-specific module objects.
        exclude_patterns: Module name segments to skip during scanning.
    """
    container.initialize(
        packages=packages,
        backend=backend,
        extra_modules=extra_modules,
        exclude_patterns=exclude_patterns,
    )
    try:
        yield
    finally:
        container.reset()


class Provide(Generic[T]):
    """Callable that resolves a type from the container.

    Use with FastAPI's ``Depends``::

        @app.get("/")
        async def index(svc: MyService = Depends(Provide(MyService))):
            ...
    """

    def __init__(self, cls: type[T]) -> None:
        self._cls = cls

    def __call__(self) -> T:
        return container.get(self._cls)
