"""Recursive package importer (component scan)."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from types import ModuleType

logger = logging.getLogger("django_autowired.scanner")

_BUILTIN_SKIP_SEGMENTS: frozenset[str] = frozenset(
    {"migrations", "tests", "test", "conftest", "factories", "fixtures"}
)


def scan_packages(
    *package_paths: str,
    exclude_patterns: set[str] | None = None,
) -> None:
    """Recursively import all sub-modules under each package, triggering @injectable side effects.

    Args:
        *package_paths: Dotted package paths to scan (e.g. ``"myapp.services"``).
        exclude_patterns: Additional module name segments to skip.
            Merged with built-in skips (migrations, tests, test, conftest, factories, fixtures).
    """
    skip = _BUILTIN_SKIP_SEGMENTS | (exclude_patterns or set())

    for pkg_path in package_paths:
        try:
            root = importlib.import_module(pkg_path)
        except ImportError:
            logger.error("Could not import root package %r — skipping.", pkg_path)
            continue
        _scan_module(root, skip)


def _scan_module(module: ModuleType, skip: frozenset[str] | set[str]) -> None:
    """Recursively import submodules of *module*, skipping excluded segments."""
    path = getattr(module, "__path__", None)
    if path is None:
        return  # not a package

    for _importer, name, _is_pkg in pkgutil.walk_packages(path, prefix=module.__name__ + "."):
        # Check if any segment of the dotted name is in the skip set
        segments = name.split(".")
        if any(seg in skip for seg in segments):
            continue

        try:
            importlib.import_module(name)
        except Exception:
            logger.warning("Failed to import %r — skipping.", name, exc_info=True)
