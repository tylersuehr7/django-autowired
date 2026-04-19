"""Tests for the registry and @injectable decorator."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod

import pytest

from django_autowired.exceptions import DuplicateBindingError
from django_autowired.registry import Registration, clear_registry, get_registry, injectable
from django_autowired.scopes import Scope


class IFoo(ABC):
    @abstractmethod
    def do(self) -> str: ...


class TestRegistration:
    def test_target_returns_cls_when_no_bind_to(self):
        class MyClass:
            pass

        reg = Registration(cls=MyClass, scope=Scope.SINGLETON)
        assert reg.target is MyClass

    def test_target_returns_bind_to_when_set(self):
        class MyImpl:
            pass

        reg = Registration(cls=MyImpl, scope=Scope.SINGLETON, bind_to=IFoo)
        assert reg.target is IFoo


class TestInjectableDecorator:
    def test_registers_concrete_class(self):
        @injectable()
        class MyService:
            pass

        regs = get_registry().all()
        assert len(regs) == 1
        assert regs[0].cls is MyService
        assert regs[0].target is MyService
        assert regs[0].scope == Scope.SINGLETON

    def test_registers_with_bind_to(self):
        @injectable(bind_to=IFoo)
        class FooImpl(IFoo):
            def do(self) -> str:
                return "foo"

        regs = get_registry().all()
        assert len(regs) == 1
        assert regs[0].cls is FooImpl
        assert regs[0].target is IFoo

    def test_custom_scope(self):
        @injectable(scope=Scope.TRANSIENT)
        class TransientService:
            pass

        regs = get_registry().all()
        assert regs[0].scope == Scope.TRANSIENT

    def test_returns_original_class_unchanged(self):
        class OriginalClass:
            x = 42

        decorated = injectable()(OriginalClass)
        assert decorated is OriginalClass
        assert decorated.x == 42

    def test_duplicate_binding_raises(self):
        @injectable(bind_to=IFoo)
        class Impl1(IFoo):
            def do(self) -> str:
                return "1"

        with pytest.raises(DuplicateBindingError) as exc_info:

            @injectable(bind_to=IFoo)
            class Impl2(IFoo):
                def do(self) -> str:
                    return "2"

        assert "Impl1" in str(exc_info.value)
        assert "Impl2" in str(exc_info.value)

    def test_idempotent_re_registration(self):
        @injectable(bind_to=IFoo)
        class FooImpl(IFoo):
            def do(self) -> str:
                return "foo"

        # Re-registering the same class should not raise
        get_registry().register(
            Registration(cls=FooImpl, scope=Scope.SINGLETON, bind_to=IFoo)
        )
        assert len(get_registry()) == 1

    def test_clear_registry(self):
        @injectable()
        class SomeClass:
            pass

        assert len(get_registry()) == 1
        clear_registry()
        assert len(get_registry()) == 0

    def test_thread_safety(self):
        """50 threads simultaneously registering different classes."""
        errors: list[Exception] = []
        classes: list[type] = []
        for i in range(50):
            cls = type(f"ThreadClass{i}", (), {})
            classes.append(cls)

        def register_class(cls: type) -> None:
            try:
                get_registry().register(
                    Registration(cls=cls, scope=Scope.SINGLETON)
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_class, args=(c,)) for c in classes]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(get_registry()) == 50
