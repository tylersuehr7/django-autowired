"""Shared pytest setup for the FastAPI demo.

Resets the container around each test. We do **not** clear the registry —
once ``@injectable`` classes are imported they stay registered for the
process lifetime, and re-importing a module is a no-op in Python. Use
``container.override(...)`` (or the ``build_container`` factory) for
per-test binding changes.
"""

import pytest

from django_autowired import container


@pytest.fixture(autouse=True)
def _isolate_container():
    container.reset()
    yield
    container.reset()
