"""Tests for the Flask demo.

Demonstrates three testing patterns:

1. Pure unit test — no container; inject mocks directly.
2. End-to-end test — whole app via Flask's test client with real wiring.
3. Partial integration — real wiring + an ``override`` for one port.
"""

from __future__ import annotations

import pytest

from django_autowired import container
from django_autowired.testing import build_container  # noqa: F401
from greetings.adapters.out_.services.friendly_greeter import FriendlyGreeter
from greetings.domain.ports.services.greeter import IGreeter
from greetings.domain.ports.services.name_formatter import INameFormatter


class FakeFormatter(INameFormatter):
    def format(self, name: str) -> str:
        return f"<{name}>"


def test_pure_unit_no_container():
    """No container — constructor-injected mocks."""
    greeter = FriendlyGreeter(FakeFormatter())
    assert greeter.greet("ada") == "hello, <ada>! welcome to django-autowired."


def test_end_to_end_real_wiring():
    """Full Flask app + Autowired extension + test client round-trip."""
    from app import create_app

    flask_app = create_app()
    with flask_app.test_client() as client:
        resp = client.get("/greet/ada/")
        assert resp.status_code == 200
        assert resp.get_json() == {
            "message": "hello, Ada! welcome to django-autowired."
        }


def test_override_with_fake_formatter(build_container):
    """Partial integration — real wiring + a fake formatter injected as override."""
    build_container(
        packages=["greetings.adapters.out_"],
        overrides={INameFormatter: FakeFormatter()},
    )
    greeter = container.get(IGreeter)
    assert greeter.greet("ada") == "hello, <ada>! welcome to django-autowired."
