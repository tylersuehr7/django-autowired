"""Testing utilities — pytest fixtures, context managers, and helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from django_autowired import container
from django_autowired.backends.base import AbstractBackend, BackendName


class ContainerFactory:
    """Callable factory for building containers in tests.

    Usage with the ``build_container`` fixture::

        def test_something(build_container):
            backend = build_container(
                packages=["myapp.services"],
                overrides={IRepo: FakeRepo},
            )
            svc = container.get(MyService)
    """

    def __call__(
        self,
        packages: list[str] | None = None,
        overrides: dict[type, Any] | None = None,
        backend: BackendName | str = "injector",
        extra_modules: list[Any] | None = None,
    ) -> AbstractBackend:
        # Note: we do NOT clear_registry() here. Python caches imported modules,
        # so clearing would strip away registrations whose modules are already
        # imported — subsequent scan_packages() calls would then be no-ops.
        # Use override() for per-test binding changes instead.
        container.reset()

        be = container.initialize(
            packages=packages or [],
            backend=backend,
            extra_modules=extra_modules,
            allow_override=True,
        )
        if overrides:
            container.override(overrides)
        return be


class InMemoryOverrideModule:
    """Wraps a dict into an ``injector.Module``-compatible callable.

    Use with ``extra_modules`` when using the injector backend::

        container.initialize(
            packages=[...],
            extra_modules=[InMemoryOverrideModule({IRepo: FakeRepo})],
        )
    """

    def __init__(self, overrides: dict[type, Any]) -> None:
        self._overrides = overrides

    def __call__(self, binder: Any) -> None:
        for iface, impl in self._overrides.items():
            if isinstance(impl, type):
                binder.bind(iface, to=impl)
            else:
                binder.bind(iface, to=impl)


@contextmanager
def container_context(
    packages: list[str] | None = None,
    backend: BackendName | str = "injector",
    overrides: dict[type, Any] | None = None,
    extra_modules: list[Any] | None = None,
) -> Iterator[AbstractBackend]:
    """Sync context manager that initializes and tears down the container.

    Usage::

        with container_context(packages=["myapp.services"]) as backend:
            svc = container.get(MyService)
    """
    container.reset()
    try:
        be = container.initialize(
            packages=packages or [],
            backend=backend,
            extra_modules=extra_modules,
            allow_override=True,
        )
        if overrides:
            container.override(overrides)
        yield be
    finally:
        container.reset()


@pytest.fixture
def autowired_container(request: pytest.FixtureRequest) -> Iterator[AbstractBackend]:
    """Pytest fixture that initializes the container from markers.

    Markers:
        ``@pytest.mark.autowired_packages(["pkg1", "pkg2"])``
        ``@pytest.mark.autowired_backend("injector")``

    Yields the initialized backend, then resets on teardown.
    """
    packages_marker = request.node.get_closest_marker("autowired_packages")
    backend_marker = request.node.get_closest_marker("autowired_backend")

    packages: list[str] = packages_marker.args[0] if packages_marker else []
    backend: str = backend_marker.args[0] if backend_marker else "injector"

    container.reset()

    be = container.initialize(
        packages=packages,
        backend=backend,
        allow_override=True,
    )
    yield be
    container.reset()


@pytest.fixture
def build_container() -> Iterator[ContainerFactory]:
    """Pytest fixture yielding a ``ContainerFactory``.

    The factory calls ``container.reset()`` before each build. After the test,
    the container is reset.
    """
    factory = ContainerFactory()
    yield factory
    container.reset()
