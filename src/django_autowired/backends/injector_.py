"""Injector backend — the priority backend for django-autowired."""

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
    import injector as _injector

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

T = TypeVar("T")

_SCOPE_MAP: dict[Scope, Any] = {}

if _AVAILABLE:
    _SCOPE_MAP = {
        Scope.SINGLETON: _injector.singleton,
        Scope.TRANSIENT: _injector.noscope,
        Scope.THREAD: _injector.threadlocal,
    }


class InjectorBackend(AbstractBackend):
    """Backend adapter for the ``injector`` library."""

    def __init__(self) -> None:
        if not _AVAILABLE:
            raise BackendNotInstalledError("injector", "injector")
        self._injector: _injector.Injector | None = None

    @classmethod
    def name(cls) -> str:
        return "injector"

    def build(
        self,
        registrations: list[Registration],
        extra_modules: list[Any] | None = None,
    ) -> None:
        modules: list[Any] = [_build_module(registrations)]
        if extra_modules:
            modules.extend(extra_modules)
        self._injector = _injector.Injector(modules)

    def get(self, cls: type[T]) -> T:
        assert self._injector is not None
        try:
            return self._injector.get(cls)
        except Exception as exc:
            raise UnresolvableTypeError(cls, str(exc)) from exc

    def override(self, bindings: dict[type, Any]) -> None:
        assert self._injector is not None

        def _override_module(binder: _injector.Binder) -> None:
            for iface, impl in bindings.items():
                if isinstance(impl, type):
                    binder.bind(iface, to=impl)
                else:
                    binder.bind(iface, to=impl)

        self._injector = self._injector.create_child_injector([_override_module])

    def raw(self) -> _injector.Injector:
        """Return the underlying ``injector.Injector``."""
        assert self._injector is not None
        return self._injector

    def create_child(self, extra_modules: list[Any] | None = None) -> _injector.Injector:
        """Create a child injector for request-scoped containers."""
        assert self._injector is not None
        return self._injector.create_child_injector(extra_modules or [])


def _build_module(registrations: list[Registration]) -> Any:
    """Create an injector.Module from a list of registrations.

    Auto-applies ``@injector.inject`` to constructors that have type-annotated
    parameters but weren't explicitly decorated, so users get Spring-style
    autowiring without decorating every ``__init__``.
    """

    def configure(binder: _injector.Binder) -> None:
        for reg in registrations:
            _auto_inject(reg.cls)
            scope = _SCOPE_MAP.get(reg.scope)
            if reg.bind_to is not None:
                binder.bind(reg.bind_to, to=reg.cls, scope=scope)
            else:
                binder.bind(reg.cls, to=reg.cls, scope=scope)

    return configure


def _auto_inject(cls: type) -> None:
    """Apply ``@injector.inject`` to *cls.__init__* if it needs dependency injection.

    Skips classes whose ``__init__`` takes no parameters beyond ``self``, and
    classes that already have the injection marker applied.
    """
    init = cls.__dict__.get("__init__")
    if init is None:
        return  # inherits default __init__ — no deps to inject

    if getattr(init, "__bindings__", None) is not None:
        return  # already decorated with @inject

    try:
        import inspect

        sig = inspect.signature(init)
    except (TypeError, ValueError):
        return

    params = [p for p in sig.parameters.values() if p.name != "self"]
    if not params:
        return  # no constructor args — no injection needed

    # Require that all parameters have annotations; otherwise leave untouched.
    if not all(p.annotation is not inspect.Parameter.empty for p in params):
        return

    setattr(cls, "__init__", _injector.inject(init))
