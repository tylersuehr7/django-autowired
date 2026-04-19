"""Backend factory and type exports."""

from __future__ import annotations

from django_autowired.backends.base import AbstractBackend, BackendName


def get_backend(name: BackendName | str) -> AbstractBackend:
    """Instantiate a backend by name.

    Args:
        name: One of ``"injector"``, ``"lagom"``, ``"wireup"``, ``"dishka"``.

    Returns:
        A new backend instance (not yet built).
    """
    if name == "injector":
        from django_autowired.backends.injector_ import InjectorBackend

        return InjectorBackend()
    if name == "lagom":
        from django_autowired.backends.lagom_ import LagomBackend

        return LagomBackend()
    if name == "wireup":
        from django_autowired.backends.wireup_ import WireupBackend

        return WireupBackend()
    if name == "dishka":
        from django_autowired.backends.dishka_ import DishkaBackend

        return DishkaBackend()
    raise ValueError(f"Unknown backend: {name!r}. Choose from: injector, lagom, wireup, dishka.")


__all__ = ["AbstractBackend", "BackendName", "get_backend"]
