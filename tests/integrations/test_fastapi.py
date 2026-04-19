"""Tests for the FastAPI integration."""

from __future__ import annotations

from unittest import mock

import pytest

fastapi_mod = pytest.importorskip("fastapi")
injector_mod = pytest.importorskip("injector")

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from django_autowired import container
from django_autowired.integrations.fastapi.lifespan import Provide, autowired_lifespan
from django_autowired.registry import injectable
from django_autowired.scopes import Scope


class TestAutowiredLifespan:
    @pytest.mark.anyio
    async def test_initializes_and_resets(self):
        app = mock.MagicMock()
        async with autowired_lifespan(app, packages=[], backend="injector"):
            assert container.is_initialized()
        assert not container.is_initialized()

    @pytest.mark.anyio
    async def test_resets_on_exception(self):
        app = mock.MagicMock()
        with pytest.raises(RuntimeError):
            async with autowired_lifespan(app, packages=[], backend="injector"):
                assert container.is_initialized()
                raise RuntimeError("boom")
        assert not container.is_initialized()


class TestProvide:
    def test_provide_resolves_from_container(self):
        @injectable()
        class MyService:
            pass

        container.initialize(packages=[], backend="injector")
        provider = Provide(MyService)
        result = provider()
        assert isinstance(result, MyService)


class TestProvideWithTestClient:
    def test_provide_in_depends(self):
        from functools import partial

        @injectable()
        class GreetService:
            def greet(self) -> str:
                return "hello from autowired"

        app = FastAPI(
            lifespan=partial(autowired_lifespan, packages=[], backend="injector")
        )

        @app.get("/")
        def index(svc: GreetService = Depends(Provide(GreetService))):
            return {"msg": svc.greet()}

        # Reset since the autouse fixture already cleared, and we need fresh state
        # for the lifespan to initialize.
        container.reset()
        from django_autowired.registry import clear_registry

        clear_registry()

        # Re-register since clearing removed the registration
        from django_autowired.registry import Registration, get_registry

        get_registry().register(
            Registration(cls=GreetService, scope=Scope.SINGLETON)
        )

        with TestClient(app) as client:
            resp = client.get("/")
            assert resp.status_code == 200
            assert resp.json()["msg"] == "hello from autowired"
