"""Global container lifecycle management."""

from __future__ import annotations

import threading
from typing import Any, TypeVar

from django_autowired.backends import get_backend
from django_autowired.backends.base import AbstractBackend, BackendName
from django_autowired.exceptions import (
    ContainerAlreadyInitializedError,
    ContainerNotInitializedError,
)
from django_autowired.registry import clear_registry, get_registry
from django_autowired.scanner import scan_packages

T = TypeVar("T")

_lock = threading.Lock()
_backend: AbstractBackend | None = None


def initialize(
    packages: list[str],
    backend: BackendName | AbstractBackend | str = "injector",
    extra_modules: list[Any] | None = None,
    exclude_patterns: set[str] | None = None,
    allow_override: bool = False,
) -> AbstractBackend:
    """Initialize the global container.

    Args:
        packages: Dotted package paths to scan for ``@injectable`` classes.
        backend: Backend name string or a pre-instantiated ``AbstractBackend``.
        extra_modules: Backend-specific module objects for manual bindings.
        exclude_patterns: Additional module name segments to skip during scanning.
        allow_override: If True, re-initialization is allowed without calling ``reset()`` first.

    Returns:
        The initialized backend instance.

    Raises:
        ContainerAlreadyInitializedError: If already initialized and ``allow_override`` is False.
    """
    global _backend  # noqa: PLW0603

    with _lock:
        if _backend is not None and not allow_override:
            raise ContainerAlreadyInitializedError()

        if _backend is not None and allow_override:
            _backend = None
            clear_registry()

        scan_packages(*packages, exclude_patterns=exclude_patterns)

        be = backend if isinstance(backend, AbstractBackend) else get_backend(backend)

        registrations = get_registry().all()
        be.build(registrations, extra_modules=extra_modules)

        _backend = be
        return be


def get(cls: type[T]) -> T:
    """Resolve a type from the container.

    Raises:
        ContainerNotInitializedError: If the container has not been initialized.
    """
    if _backend is None:
        raise ContainerNotInitializedError()
    return _backend.get(cls)


def get_backend_instance() -> AbstractBackend:
    """Return the current backend instance.

    Raises:
        ContainerNotInitializedError: If the container has not been initialized.
    """
    if _backend is None:
        raise ContainerNotInitializedError()
    return _backend


def override(bindings: dict[type, Any]) -> None:
    """Override bindings in the current container.

    Raises:
        ContainerNotInitializedError: If the container has not been initialized.
    """
    if _backend is None:
        raise ContainerNotInitializedError()
    _backend.override(bindings)


def reset() -> None:
    """Tear down the container and clear the registry. For tests only."""
    global _backend  # noqa: PLW0603
    with _lock:
        _backend = None
        clear_registry()


def is_initialized() -> bool:
    """Return whether the container has been initialized."""
    return _backend is not None
