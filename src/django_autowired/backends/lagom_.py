"""Lagom backend adapter."""

from __future__ import annotations

from typing import Any, TypeVar

from django_autowired.backends.base import AbstractBackend
from django_autowired.exceptions import (
    BackendNotInstalledError,
    UnresolvableTypeError,
)
from django_autowired.registry import Registration
from django_autowired.scopes import Scope

try:
    import lagom

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

T = TypeVar("T")


class LagomBackend(AbstractBackend):
    """Backend adapter for the ``lagom`` library.

    Lagom resolves concrete classes automatically from type hints, so only
    interface bindings and singleton scopes need explicit registration.

    Note:
        The ``@inject`` decorator from the ``injector`` library is not used
        or needed with this backend.
    """

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise BackendNotInstalledError("lagom", "lagom")
        self._container: lagom.Container | None = None
        self._overrides: dict[type, Any] = {}

    @classmethod
    def name(cls) -> str:
        return "lagom"

    def build(
        self,
        registrations: list[Registration],
        extra_modules: list[Any] | None = None,
    ) -> None:
        container = lagom.Container()

        for reg in registrations:
            if reg.bind_to is not None:
                if reg.scope == Scope.SINGLETON:
                    container.define(reg.bind_to, lagom.Singleton(reg.cls))
                else:
                    container.define(reg.bind_to, lambda _c, cls=reg.cls: cls())
            elif reg.scope == Scope.SINGLETON:
                container.define(reg.cls, lagom.Singleton(reg.cls))

        self._container = container
        self._overrides.clear()

    def get(self, cls: type[T]) -> T:
        if cls in self._overrides:
            return self._overrides[cls]
        assert self._container is not None
        try:
            return self._container.resolve(cls)
        except Exception as exc:
            raise UnresolvableTypeError(cls, str(exc)) from exc

    def override(self, bindings: dict[type, Any]) -> None:
        """Apply overrides via a per-instance dict.

        Lagom's ``define`` raises on duplicate bindings, so overrides are
        stored in a dict and consulted before delegating to the container.
        """
        for iface, impl in bindings.items():
            if isinstance(impl, type):
                try:
                    self._overrides[iface] = impl()
                except Exception:
                    assert self._container is not None
                    self._overrides[iface] = self._container.resolve(impl)
            else:
                self._overrides[iface] = impl

    def raw(self) -> lagom.Container:
        """Return the underlying ``lagom.Container``."""
        assert self._container is not None
        return self._container
