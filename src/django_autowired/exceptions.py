"""Typed, actionable exceptions for django-autowired."""

from __future__ import annotations

from typing import Any


class AutowiredError(Exception):
    """Base exception for all django-autowired errors."""


class ContainerNotInitializedError(AutowiredError):
    """Raised when the container is accessed before ``initialize()`` is called."""

    def __init__(self) -> None:
        super().__init__(
            "Container has not been initialized. "
            "Call django_autowired.container.initialize() first, or use "
            "AutowiredAppConfig.ready() in Django."
        )


class ContainerAlreadyInitializedError(AutowiredError):
    """Raised when ``initialize()`` is called twice without ``reset()``."""

    def __init__(self) -> None:
        super().__init__(
            "Container is already initialized. Call django_autowired.container.reset() "
            "before re-initializing, or pass allow_override=True."
        )


class DuplicateBindingError(AutowiredError):
    """Raised when two different classes bind to the same interface."""

    def __init__(self, interface: type, existing_cls: type, new_cls: type) -> None:
        self.interface = interface
        self.existing_cls = existing_cls
        self.new_cls = new_cls
        super().__init__(
            f"Duplicate binding for {_name(interface)}: "
            f"{_name(existing_cls)} is already registered, "
            f"cannot also register {_name(new_cls)}. "
            f"Use extra_modules to conditionally swap implementations."
        )


class BackendNotInstalledError(AutowiredError):
    """Raised when the selected backend package is not installed."""

    def __init__(self, backend_name: str, package: str) -> None:
        self.backend_name = backend_name
        self.package = package
        super().__init__(
            f"Backend '{backend_name}' requires the '{package}' package. "
            f'Install it with: pip install "django-autowired[{backend_name}]"'
        )


class UnresolvableTypeError(AutowiredError):
    """Raised when the container cannot satisfy a type."""

    def __init__(self, cls: Any, reason: str) -> None:
        self.cls = cls
        self.reason = reason
        super().__init__(
            f"Cannot resolve {_name(cls)}: {reason}. "
            f"Make sure the class is decorated with @injectable or registered "
            f"via extra_modules."
        )


def _name(obj: Any) -> str:
    """Return a qualified name for display."""
    if hasattr(obj, "__qualname__"):
        mod = getattr(obj, "__module__", "")
        return f"{mod}.{obj.__qualname__}" if mod else obj.__qualname__
    return repr(obj)
