"""Tests for exception types and messages."""

from __future__ import annotations

from django_autowired.exceptions import (
    AutowiredError,
    BackendNotInstalledError,
    ContainerAlreadyInitializedError,
    ContainerNotInitializedError,
    DuplicateBindingError,
    UnresolvableTypeError,
)


class TestExceptionHierarchy:
    def test_all_are_autowired_errors(self):
        assert issubclass(ContainerNotInitializedError, AutowiredError)
        assert issubclass(ContainerAlreadyInitializedError, AutowiredError)
        assert issubclass(DuplicateBindingError, AutowiredError)
        assert issubclass(BackendNotInstalledError, AutowiredError)
        assert issubclass(UnresolvableTypeError, AutowiredError)


class TestExceptionMessages:
    def test_container_not_initialized(self):
        exc = ContainerNotInitializedError()
        msg = str(exc)
        assert "initialize" in msg.lower()

    def test_container_already_initialized(self):
        exc = ContainerAlreadyInitializedError()
        msg = str(exc)
        assert "reset" in msg.lower()

    def test_duplicate_binding_contains_all_types(self):
        class IFoo:
            pass

        class Impl1:
            pass

        class Impl2:
            pass

        exc = DuplicateBindingError(IFoo, Impl1, Impl2)
        msg = str(exc)
        assert "IFoo" in msg
        assert "Impl1" in msg
        assert "Impl2" in msg

    def test_backend_not_installed_contains_instructions(self):
        exc = BackendNotInstalledError("injector", "injector")
        msg = str(exc)
        assert "injector" in msg
        assert "pip install" in msg

    def test_unresolvable_type_contains_class_name(self):
        class MyService:
            pass

        exc = UnresolvableTypeError(MyService, "no binding found")
        msg = str(exc)
        assert "MyService" in msg
        assert "no binding found" in msg
