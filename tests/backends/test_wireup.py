"""Tests for the wireup backend."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

wireup_mod = pytest.importorskip("wireup")

from django_autowired import container
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

        container.initialize(packages=[], backend="wireup")
        svc = container.get(SimpleService)
        assert isinstance(svc, SimpleService)


class TestInterfaceResolution:
    def test_resolve_interface(self):
        @injectable(bind_to=IGreeter)
        class HelloGreeter(IGreeter):
            def greet(self) -> str:
                return "hello"

        container.initialize(packages=[], backend="wireup")
        result = container.get(IGreeter)
        assert isinstance(result, HelloGreeter)
        assert result.greet() == "hello"


class TestSingletonScope:
    def test_singleton(self):
        @injectable(scope=Scope.SINGLETON)
        class SingletonSvc:
            pass

        container.initialize(packages=[], backend="wireup")
        assert container.get(SingletonSvc) is container.get(SingletonSvc)


class TestOverride:
    def test_override_with_class(self):
        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "real"

        class FakeGreeter(IGreeter):
            def greet(self) -> str:
                return "fake"

        container.initialize(packages=[], backend="wireup")
        container.override({IGreeter: FakeGreeter()})
        assert container.get(IGreeter).greet() == "fake"

    def test_override_with_instance(self):
        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "real"

        class StubGreeter(IGreeter):
            def greet(self) -> str:
                return "stub"

        container.initialize(packages=[], backend="wireup")
        container.override({IGreeter: StubGreeter()})
        assert container.get(IGreeter).greet() == "stub"


class TestThreadFallback:
    def test_thread_scope_does_not_error(self):
        @injectable(scope=Scope.THREAD)
        class ThreadSvc:
            pass

        container.initialize(packages=[], backend="wireup")
        svc = container.get(ThreadSvc)
        assert isinstance(svc, ThreadSvc)
