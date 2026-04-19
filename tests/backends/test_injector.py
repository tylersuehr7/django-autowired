"""Tests for the injector backend — the most thorough backend test suite."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

injector_mod = pytest.importorskip("injector")

from django_autowired import container
from django_autowired.backends.injector_ import InjectorBackend
from django_autowired.exceptions import UnresolvableTypeError
from django_autowired.registry import Registration, get_registry
from django_autowired.scopes import Scope


class IGreeter(ABC):
    @abstractmethod
    def greet(self) -> str: ...


class IRepo(ABC):
    @abstractmethod
    def fetch(self) -> str: ...


# Module-level classes for tests that depend on type hint resolution.
# Classes defined inside test function bodies cannot be resolved by
# ``typing.get_type_hints`` because their names are not in the enclosing
# module's globals.


class ConcreteService:
    pass


class HelloGreeter(IGreeter):
    def greet(self) -> str:
        return "hello"


class ChainC:
    pass


class ChainB:
    @injector_mod.inject
    def __init__(self, c: ChainC) -> None:
        self.c = c


class ChainA:
    @injector_mod.inject
    def __init__(self, b: ChainB) -> None:
        self.b = b


class SingletonSvc:
    pass


class TransientSvc:
    pass


class DefaultGreeter(IGreeter):
    def greet(self) -> str:
        return "default"


class OverrideGreeter(IGreeter):
    def greet(self) -> str:
        return "override"


class RealGreeter(IGreeter):
    def greet(self) -> str:
        return "real"


class FakeGreeter(IGreeter):
    def greet(self) -> str:
        return "fake"


class InjectDep:
    pass


class InjectConsumer:
    @injector_mod.inject
    def __init__(self, dep: InjectDep) -> None:
        self.dep = dep


class NoInjectDep:
    pass


class NoInjectConsumer:
    def __init__(self, dep: NoInjectDep) -> None:
        self.dep = dep


def _register(*regs: Registration) -> None:
    for r in regs:
        get_registry().register(r)


class TestConcreteResolution:
    def test_resolve_concrete_class(self):
        _register(Registration(cls=ConcreteService, scope=Scope.SINGLETON))
        container.initialize(packages=[], backend="injector")
        svc = container.get(ConcreteService)
        assert isinstance(svc, ConcreteService)


class TestInterfaceResolution:
    def test_resolve_interface_to_concrete(self):
        _register(
            Registration(cls=HelloGreeter, scope=Scope.SINGLETON, bind_to=IGreeter)
        )
        container.initialize(packages=[], backend="injector")
        result = container.get(IGreeter)
        assert isinstance(result, HelloGreeter)
        assert result.greet() == "hello"


class TestTransitiveInjection:
    def test_chain_a_b_c(self):
        _register(
            Registration(cls=ChainA, scope=Scope.SINGLETON),
            Registration(cls=ChainB, scope=Scope.SINGLETON),
            Registration(cls=ChainC, scope=Scope.SINGLETON),
        )
        container.initialize(packages=[], backend="injector")
        a = container.get(ChainA)
        assert isinstance(a.b, ChainB)
        assert isinstance(a.b.c, ChainC)


class TestSingletonReuse:
    def test_singleton_returns_same_instance(self):
        _register(Registration(cls=SingletonSvc, scope=Scope.SINGLETON))
        container.initialize(packages=[], backend="injector")
        assert container.get(SingletonSvc) is container.get(SingletonSvc)


class TestTransientFresh:
    def test_transient_returns_new_instances(self):
        _register(Registration(cls=TransientSvc, scope=Scope.TRANSIENT))
        container.initialize(packages=[], backend="injector")
        assert container.get(TransientSvc) is not container.get(TransientSvc)


class TestExtraModules:
    def test_extra_module_overrides_binding(self):
        _register(
            Registration(cls=DefaultGreeter, scope=Scope.SINGLETON, bind_to=IGreeter)
        )

        def override_module(binder: injector_mod.Binder) -> None:
            binder.bind(IGreeter, to=OverrideGreeter)

        container.initialize(
            packages=[], backend="injector", extra_modules=[override_module]
        )
        assert container.get(IGreeter).greet() == "override"


class TestOverride:
    def test_override_replaces_binding(self):
        _register(
            Registration(cls=RealGreeter, scope=Scope.SINGLETON, bind_to=IGreeter)
        )
        container.initialize(packages=[], backend="injector")
        assert container.get(IGreeter).greet() == "real"

        container.override({IGreeter: FakeGreeter})
        assert container.get(IGreeter).greet() == "fake"


class TestRaw:
    def test_raw_returns_injector(self):
        container.initialize(packages=[], backend="injector")
        be = container.get_backend_instance()
        assert isinstance(be, InjectorBackend)
        assert isinstance(be.raw(), injector_mod.Injector)


class TestCreateChild:
    def test_child_injector(self):
        container.initialize(packages=[], backend="injector")
        be = container.get_backend_instance()
        assert isinstance(be, InjectorBackend)
        child = be.create_child()
        assert isinstance(child, injector_mod.Injector)


class TestInjectAnnotation:
    def test_inject_constructor(self):
        _register(
            Registration(cls=InjectDep, scope=Scope.SINGLETON),
            Registration(cls=InjectConsumer, scope=Scope.SINGLETON),
        )
        container.initialize(packages=[], backend="injector")
        c = container.get(InjectConsumer)
        assert isinstance(c.dep, InjectDep)

    def test_constructor_without_inject_still_resolves(self):
        _register(
            Registration(cls=NoInjectDep, scope=Scope.SINGLETON),
            Registration(cls=NoInjectConsumer, scope=Scope.SINGLETON),
        )
        container.initialize(packages=[], backend="injector")
        c = container.get(NoInjectConsumer)
        assert isinstance(c.dep, NoInjectDep)


class TestUnresolvableType:
    def test_unregistered_type_raises(self):
        class NotRegistered:
            def __init__(self, x: int) -> None:
                self.x = x

        container.initialize(packages=[], backend="injector")
        with pytest.raises(UnresolvableTypeError):
            container.get(NotRegistered)
