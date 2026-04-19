"""Tests for the lagom backend."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

lagom_mod = pytest.importorskip("lagom")

from django_autowired import container
from django_autowired.backends.lagom_ import LagomBackend
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

        container.initialize(packages=[], backend="lagom")
        svc = container.get(SimpleService)
        assert isinstance(svc, SimpleService)


class TestInterfaceResolution:
    def test_resolve_interface(self):
        @injectable(bind_to=IGreeter)
        class HelloGreeter(IGreeter):
            def greet(self) -> str:
                return "hello"

        container.initialize(packages=[], backend="lagom")
        result = container.get(IGreeter)
        assert isinstance(result, HelloGreeter)
        assert result.greet() == "hello"


class TestSingletonScope:
    def test_singleton_reuses_instance(self):
        @injectable(scope=Scope.SINGLETON)
        class SingletonSvc:
            pass

        container.initialize(packages=[], backend="lagom")
        assert container.get(SingletonSvc) is container.get(SingletonSvc)


class TestTransientScope:
    def test_transient_creates_new(self):
        @injectable(scope=Scope.TRANSIENT)
        class TransientSvc:
            pass

        container.initialize(packages=[], backend="lagom")
        assert container.get(TransientSvc) is not container.get(TransientSvc)


class TestOverride:
    def test_override_with_class(self):
        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "real"

        class FakeGreeter(IGreeter):
            def greet(self) -> str:
                return "fake"

        container.initialize(packages=[], backend="lagom")
        assert container.get(IGreeter).greet() == "real"

        container.override({IGreeter: FakeGreeter})
        assert container.get(IGreeter).greet() == "fake"

    def test_override_with_instance(self):
        @injectable(bind_to=IGreeter)
        class RealGreeter(IGreeter):
            def greet(self) -> str:
                return "real"

        class FakeGreeter(IGreeter):
            def greet(self) -> str:
                return "instance"

        container.initialize(packages=[], backend="lagom")
        container.override({IGreeter: FakeGreeter()})
        result = container.get(IGreeter)
        assert result.greet() == "instance"


class TestRaw:
    def test_raw_returns_lagom_container(self):
        container.initialize(packages=[], backend="lagom")
        be = container.get_backend_instance()
        assert isinstance(be, LagomBackend)
        assert isinstance(be.raw(), lagom_mod.Container)
