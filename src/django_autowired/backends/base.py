"""Abstract base class for DI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, TypeVar

T = TypeVar("T")

BackendName = Literal["injector", "lagom", "wireup", "dishka"]


class AbstractBackend(ABC):
    """Backend contract that all DI library adapters must implement."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Return the canonical backend name."""

    @abstractmethod
    def build(
        self,
        registrations: list[Any],
        extra_modules: list[Any] | None = None,
    ) -> None:
        """Configure the native container from the registration list."""

    @abstractmethod
    def get(self, cls: type[T]) -> T:
        """Resolve an instance of *cls* from the native container."""

    @abstractmethod
    def override(self, bindings: dict[type, Any]) -> None:
        """Apply replacement bindings to the container."""

    @abstractmethod
    def raw(self) -> Any:
        """Return the underlying native container for advanced use."""
