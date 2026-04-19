"""Tests for the container lifecycle."""

from __future__ import annotations

import pytest

from django_autowired import container
from django_autowired.exceptions import (
    ContainerAlreadyInitializedError,
    ContainerNotInitializedError,
)
from django_autowired.registry import injectable

injector_mod = pytest.importorskip("injector")


class TestContainerLifecycle:
    def test_get_before_initialize_raises(self):
        class Foo:
            pass

        with pytest.raises(ContainerNotInitializedError):
            container.get(Foo)

    def test_double_initialize_raises(self):
        container.initialize(packages=[], backend="injector")
        with pytest.raises(ContainerAlreadyInitializedError):
            container.initialize(packages=[], backend="injector")

    def test_allow_override_permits_reinit(self):
        container.initialize(packages=[], backend="injector")
        be = container.initialize(packages=[], backend="injector", allow_override=True)
        assert be is not None

    def test_reset_then_initialize(self):
        container.initialize(packages=[], backend="injector")
        container.reset()
        be = container.initialize(packages=[], backend="injector")
        assert be is not None

    def test_is_initialized(self):
        assert container.is_initialized() is False
        container.initialize(packages=[], backend="injector")
        assert container.is_initialized() is True
        container.reset()
        assert container.is_initialized() is False

    def test_override_before_init_raises(self):
        with pytest.raises(ContainerNotInitializedError):
            container.override({})

    def test_get_backend_instance_returns_backend(self):
        be = container.initialize(packages=[], backend="injector")
        assert container.get_backend_instance() is be

    def test_pre_instantiated_backend(self):
        from django_autowired.backends.injector_ import InjectorBackend

        be = InjectorBackend()
        result = container.initialize(packages=[], backend=be)
        assert result is be
        assert container.get_backend_instance() is be


class TestContainerResolution:
    def test_resolve_registered_class(self):
        @injectable()
        class SimpleService:
            pass

        container.initialize(packages=[], backend="injector")
        svc = container.get(SimpleService)
        assert isinstance(svc, SimpleService)

    def test_override_replaces_binding(self):
        from abc import ABC, abstractmethod

        class IGreeter(ABC):
            @abstractmethod
            def greet(self) -> str: ...

        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "hello"

        class FakeGreeter(IGreeter):
            def greet(self) -> str:
                return "fake"

        container.initialize(packages=[], backend="injector")
        assert container.get(IGreeter).greet() == "hello"

        container.override({IGreeter: FakeGreeter})
        assert container.get(IGreeter).greet() == "fake"
