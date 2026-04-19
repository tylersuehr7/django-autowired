"""Injectable decorator and thread-safe registration store."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from django_autowired.exceptions import DuplicateBindingError
from django_autowired.scopes import Scope


@dataclass(frozen=True)
class Registration:
    """A single injectable registration.

    Attributes:
        cls: The concrete implementation class.
        scope: The lifecycle scope for this registration.
        bind_to: Optional interface/ABC this class implements.
    """

    cls: type
    scope: Scope
    bind_to: type | None = None

    @property
    def target(self) -> type:
        """The type key used for container binding — ``bind_to`` if set, else ``cls``."""
        return self.bind_to if self.bind_to is not None else self.cls


class _Registry:
    """Thread-safe store of all ``@injectable`` registrations."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._registrations: list[Registration] = []
        self._target_map: dict[type, Registration] = {}

    def register(self, registration: Registration) -> None:
        """Add a registration, raising on duplicate interface bindings."""
        with self._lock:
            existing = self._target_map.get(registration.target)
            if existing is not None:
                if existing.cls is registration.cls:
                    return  # idempotent re-registration
                raise DuplicateBindingError(
                    registration.target, existing.cls, registration.cls
                )
            self._registrations.append(registration)
            self._target_map[registration.target] = registration

    def all(self) -> list[Registration]:
        """Return a snapshot of all registrations."""
        with self._lock:
            return list(self._registrations)

    def clear(self) -> None:
        """Remove all registrations."""
        with self._lock:
            self._registrations.clear()
            self._target_map.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._registrations)


_registry = _Registry()


def get_registry() -> _Registry:
    """Return the module-level registry singleton."""
    return _registry


def clear_registry() -> None:
    """Clear all registrations. For tests only."""
    _registry.clear()


def injectable(
    scope: Scope = Scope.SINGLETON,
    bind_to: type | None = None,
) -> Any:
    """Decorator that registers a class for autowiring.

    Args:
        scope: Lifecycle scope (default: SINGLETON).
        bind_to: Optional interface type to bind this implementation to.

    Returns:
        The original class, unmodified.

    Example::

        @injectable()
        class MyService:
            ...

        @injectable(bind_to=IRepository, scope=Scope.TRANSIENT)
        class SqlRepository:
            ...
    """

    def decorator(cls: type) -> type:
        _registry.register(Registration(cls=cls, scope=scope, bind_to=bind_to))
        return cls

    return decorator
