"""Dishka backend adapter."""

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
    from dishka import Provider, make_container
    from dishka import Scope as DishkaScope

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

T = TypeVar("T")

_SCOPE_MAP: dict[Scope, Any] = {}

if _AVAILABLE:
    _SCOPE_MAP = {
        Scope.SINGLETON: DishkaScope.APP,
        Scope.TRANSIENT: DishkaScope.APP,
        Scope.THREAD: DishkaScope.APP,
    }


class DishkaBackend(AbstractBackend):
    """Backend adapter for the ``dishka`` library.

    Note:
        Dishka's scope model differs from other backends — ``SINGLETON``,
        ``TRANSIENT``, and ``THREAD`` all map to ``DishkaScope.APP`` because
        the top-level container is APP-scoped. Use ``cache=False`` semantics
        via a ``REQUEST`` scope for true transient behavior if needed.
    """

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise BackendNotInstalledError("dishka", "dishka")
        self._container: Any = None
        self._registrations: list[Registration] = []

    @classmethod
    def name(cls) -> str:
        return "dishka"

    def build(
        self,
        registrations: list[Registration],
        extra_modules: list[Any] | None = None,
    ) -> None:
        self._registrations = list(registrations)
        provider = _build_provider(registrations)
        providers = [provider] + list(extra_modules or [])
        self._container = make_container(*providers)

    def get(self, cls: type[T]) -> T:
        assert self._container is not None
        try:
            return self._container.get(cls)
        except Exception as exc:
            raise UnresolvableTypeError(cls, str(exc)) from exc

    def override(self, bindings: dict[type, Any]) -> None:
        assert self._container is not None
        self._container.close()
        base = _build_provider(self._registrations)
        override = _build_override_provider(bindings)
        self._container = make_container(base, override)

    def raw(self) -> Any:
        """Return the underlying dishka ``Container``."""
        assert self._container is not None
        return self._container


def _build_provider(registrations: list[Registration]) -> Provider:
    """Build a dishka Provider from registrations."""
    provider = Provider(scope=DishkaScope.APP)

    for reg in registrations:
        target = reg.bind_to if reg.bind_to is not None else reg.cls
        provider.provide(
            _make_factory(reg.cls),
            provides=target,
            scope=DishkaScope.APP,
            cache=(reg.scope == Scope.SINGLETON),
        )

    return provider


def _build_override_provider(bindings: dict[type, Any]) -> Provider:
    """Build a dishka Provider that overrides existing bindings."""
    provider = Provider(scope=DishkaScope.APP)

    for iface, impl in bindings.items():
        if isinstance(impl, type):
            provider.provide(
                _make_factory(impl),
                provides=iface,
                scope=DishkaScope.APP,
                override=True,
            )
        else:
            provider.provide(
                _make_instance_factory(impl),
                provides=iface,
                scope=DishkaScope.APP,
                override=True,
            )

    return provider


def _make_factory(cls: type) -> Any:
    """Return a zero-arg factory callable whose return annotation is *cls*."""

    def factory() -> Any:
        return cls()

    factory.__annotations__ = {"return": cls}
    return factory


def _make_instance_factory(instance: Any) -> Any:
    """Return a zero-arg factory callable that yields *instance*."""

    def factory() -> Any:
        return instance

    factory.__annotations__ = {"return": type(instance)}
    return factory
