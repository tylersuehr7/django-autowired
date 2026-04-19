"""Wireup backend adapter (wireup >= 2.9)."""

from __future__ import annotations

import logging
from typing import Any, Literal, TypeVar

from django_autowired.backends.base import AbstractBackend
from django_autowired.exceptions import (
    BackendNotInstalledError,
    UnresolvableTypeError,
)
from django_autowired.registry import Registration
from django_autowired.scopes import Scope

try:
    import wireup

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

T = TypeVar("T")

logger = logging.getLogger("django_autowired.backends.wireup")


class WireupBackend(AbstractBackend):
    """Backend adapter for the ``wireup`` library.

    Note:
        ``Scope.THREAD`` falls back to ``SINGLETON`` because wireup does not
        support thread-local scoping, and transient resolution from the root
        container requires explicit scope entry — which breaks the simple
        ``container.get()`` contract. ``Scope.TRANSIENT`` is still honored,
        but consumers must enter a scope to resolve transient injectables.
    """

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise BackendNotInstalledError("wireup", "wireup")
        self._container: Any = None
        self._overrides: dict[type, Any] = {}

    @classmethod
    def name(cls) -> str:
        return "wireup"

    def build(
        self,
        registrations: list[Registration],
        extra_modules: list[Any] | None = None,
    ) -> None:
        injectables: list[Any] = []

        for reg in registrations:
            lifetime = self._map_scope(reg.scope)
            decorated = wireup.injectable(
                lifetime=lifetime,
                as_type=reg.bind_to,
            )(reg.cls)
            injectables.append(decorated)

        self._container = wireup.create_sync_container(
            injectables=injectables + (extra_modules or []),
        )
        self._overrides.clear()

    def get(self, cls: type[T]) -> T:
        if cls in self._overrides:
            return self._overrides[cls]
        assert self._container is not None
        try:
            return self._container.get(cls)
        except Exception as exc:
            raise UnresolvableTypeError(cls, str(exc)) from exc

    def override(self, bindings: dict[type, Any]) -> None:
        for iface, impl in bindings.items():
            if isinstance(impl, type):
                try:
                    self._overrides[iface] = impl()
                except Exception:
                    self._overrides[iface] = self.get(impl)
            else:
                self._overrides[iface] = impl

    def raw(self) -> Any:
        """Return the underlying ``wireup.SyncContainer``."""
        assert self._container is not None
        return self._container

    @staticmethod
    def _map_scope(scope: Scope) -> Literal["singleton", "scoped", "transient"]:
        if scope == Scope.THREAD:
            logger.debug(
                "Scope.THREAD is not supported by wireup — falling back to SINGLETON."
            )
            return "singleton"
        if scope == Scope.SINGLETON:
            return "singleton"
        return "transient"
