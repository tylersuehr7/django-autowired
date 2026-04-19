"""Tests for the dishka backend."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

dishka_mod = pytest.importorskip("dishka")

from django_autowired import container
from django_autowired.backends.dishka_ import DishkaBackend
from django_autowired.registry import injectable
from django_autowired.scopes import Scope


class IGreeter(ABC):
    @abstractmethod
    def greet(self) -> str: ...


class TestConcreteResolution:
    def test_resolve_concrete(self):
        @injectable()
        class SimpleService:
            pass

        container.initialize(packages=[], backend="dishka")
        svc = container.get(SimpleService)
        assert isinstance(svc, SimpleService)


class TestInterfaceResolution:
    def test_resolve_interface(self):
        @injectable(bind_to=IGreeter)
        class HelloGreeter(IGreeter):
            def greet(self) -> str:
                return "hello"

        container.initialize(packages=[], backend="dishka")
        result = container.get(IGreeter)
        assert isinstance(result, HelloGreeter)
        assert result.greet() == "hello"


class TestSingletonScope:
    def test_singleton_reuses(self):
        @injectable(scope=Scope.SINGLETON)
        class SingletonSvc:
            pass

        container.initialize(packages=[], backend="dishka")
        assert container.get(SingletonSvc) is container.get(SingletonSvc)


class TestOverride:
    def test_override_rebuilds_container(self):
        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "real"

        class FakeGreeter(IGreeter):
            def greet(self) -> str:
                return "fake"

        container.initialize(packages=[], backend="dishka")
        assert container.get(IGreeter).greet() == "real"

        container.override({IGreeter: FakeGreeter})
        assert container.get(IGreeter).greet() == "fake"


class TestRaw:
    def test_raw_returns_dishka_container(self):
        container.initialize(packages=[], backend="dishka")
        be = container.get_backend_instance()
        assert isinstance(be, DishkaBackend)
        raw = be.raw()
        assert raw is not None
