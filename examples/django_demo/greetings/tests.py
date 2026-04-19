"""Tests for the greetings app.

Demonstrates three testing patterns:

1. Pure unit test — no container; inject mocks directly.
2. Integration test — use ``autowired_container`` fixture + markers.
3. Partial integration — use ``build_container`` with overrides.
"""

from __future__ import annotations

import pytest

from django_autowired import container
from django_autowired.testing import autowired_container, build_container  # noqa: F401
from greetings.domain.ports.services.greeter import IGreeter
from greetings.domain.ports.services.name_formatter import INameFormatter
from greetings.adapters.out_.services.friendly_greeter import FriendlyGreeter


class FakeFormatter(INameFormatter):
    def format(self, name: str) -> str:
        return f"<{name}>"


def test_pure_unit_no_container():
    """No container — constructor-injected mocks."""
    greeter = FriendlyGreeter(FakeFormatter())
    assert greeter.greet("ada") == "hello, <ada>! welcome to django-autowired."


@pytest.mark.autowired_packages(["greetings.adapters.out_"])
@pytest.mark.autowired_backend("injector")
def test_full_wiring(autowired_container):
    """Real autowiring — scans packages and builds the container."""
    greeter = container.get(IGreeter)
    assert "ada" in greeter.greet("ada").lower()
    # TitleCaseFormatter capitalizes "ada" to "Ada"
    assert "Ada" in greeter.greet("ada")


def test_override_with_fake_formatter(build_container):
    """Partial integration — real wiring + a fake formatter."""
    build_container(
        packages=["greetings.adapters.out_"],
        overrides={INameFormatter: FakeFormatter()},
    )
    greeter = container.get(IGreeter)
    assert greeter.greet("ada") == "hello, <ada>! welcome to django-autowired."
