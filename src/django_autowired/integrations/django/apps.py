"""Django AppConfig that autowires injectable classes at startup."""

from __future__ import annotations

import warnings
from typing import Any

try:
    from django.apps import AppConfig
except ImportError as exc:
    raise ImportError(
        "Django is required for the Django integration. "
        'Install it with: pip install "django-autowired[django]"'
    ) from exc

from django_autowired import container


class AutowiredAppConfig(AppConfig):
    """Base AppConfig that initializes the autowired container in ``ready()``.

    Subclass this and set the class attributes to configure scanning::

        class MyAppConfig(AutowiredAppConfig):
            name = "myapp"
            autowired_packages = ["myapp.services", "myapp.adapters"]
            autowired_backend = "injector"

    Attributes:
        autowired_packages: Package paths to scan for ``@injectable`` classes.
        autowired_backend: Backend name (default: ``"injector"``).
        autowired_extra_modules: Backend-specific modules for manual bindings.
        autowired_exclude_patterns: Additional module segments to skip during scanning.
    """

    autowired_packages: list[str] = []
    autowired_backend: str = "injector"
    autowired_extra_modules: list[Any] = []
    autowired_exclude_patterns: set[str] = set()

    def ready(self) -> None:
        super().ready()

        if not self.autowired_packages:
            warnings.warn(
                f"{type(self).__name__}.autowired_packages is empty — "
                f"no packages will be scanned for @injectable classes.",
                UserWarning,
                stacklevel=1,
            )

        container.initialize(
            packages=self.autowired_packages,
            backend=self.autowired_backend,
            extra_modules=self.autowired_extra_modules or None,
            exclude_patterns=self.autowired_exclude_patterns or None,
        )
