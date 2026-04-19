"""Tests for the Flask integration."""

from __future__ import annotations

import pytest

flask_mod = pytest.importorskip("flask")
injector_mod = pytest.importorskip("injector")

from flask import Flask

from django_autowired import container
from django_autowired.integrations.flask.extension import Autowired, inject_dep
from django_autowired.registry import injectable


class TestAutowiredDirect:
    def test_direct_init_initializes_container(self):
        @injectable()
        class FlaskService:
            pass

        app = Flask(__name__)
        Autowired(app, packages=[], backend="injector")
        assert container.is_initialized()


class TestAutowiredFactory:
    def test_init_app_factory_pattern(self):
        @injectable()
        class FlaskService:
            pass

        aw = Autowired(packages=[], backend="injector")
        app = Flask(__name__)
        aw.init_app(app)
        assert container.is_initialized()

    def test_init_app_args_take_precedence(self):
        """init_app() args override constructor args."""

        @injectable()
        class FlaskService:
            pass

        aw = Autowired(packages=["wrong"], backend="lagom")
        app = Flask(__name__)
        aw.init_app(app, packages=[], backend="injector")

        be = container.get_backend_instance()
        assert be.name() == "injector"


class TestInjectDep:
    def test_resolves_from_container(self):
        @injectable()
        class DepService:
            def value(self) -> str:
                return "resolved"

        app = Flask(__name__)
        Autowired(app, packages=[], backend="injector")

        with app.app_context():
            svc = inject_dep(DepService)
            assert svc.value() == "resolved"
