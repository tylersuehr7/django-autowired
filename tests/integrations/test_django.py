"""Tests for the Django integration."""

from __future__ import annotations

import sys
import types
import warnings
from unittest import mock

import pytest

django_mod = pytest.importorskip("django")
injector_mod = pytest.importorskip("injector")

import django.conf

if not django.conf.settings.configured:
    django.conf.settings.configure(
        INSTALLED_APPS=[],
        DATABASES={},
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )

import django as _django

_django.setup()

from django_autowired import container
from django_autowired.integrations.django.apps import AutowiredAppConfig


def _make_fake_app_module(name: str, path: str = "/tmp/fake_app_path") -> types.ModuleType:
    """Create a fake module object with a filesystem path for AppConfig.__init__."""
    mod = types.ModuleType(name)
    mod.__file__ = f"{path}/__init__.py"
    mod.__path__ = [path]
    sys.modules[name] = mod
    return mod


class TestAutowiredAppConfig:
    def test_ready_calls_initialize(self):
        mod = _make_fake_app_module("ready_app")

        class MyAppConfig(AutowiredAppConfig):
            name = "ready_app"
            autowired_packages = ["myapp.services"]
            autowired_backend = "injector"

        config = MyAppConfig("ready_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            config.ready()
            mock_init.assert_called_once_with(
                packages=["myapp.services"],
                backend="injector",
                extra_modules=None,
                exclude_patterns=None,
            )

    def test_empty_packages_emits_warning(self):
        mod = _make_fake_app_module("empty_app")

        class EmptyConfig(AutowiredAppConfig):
            name = "empty_app"
            autowired_packages = []

        config = EmptyConfig("empty_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config.ready()
                assert len(w) == 1
                assert "empty" in str(w[0].message).lower()

    def test_backend_attribute_is_used(self):
        mod = _make_fake_app_module("lagom_app")

        class LagomConfig(AutowiredAppConfig):
            name = "lagom_app"
            autowired_packages = ["pkg"]
            autowired_backend = "lagom"

        config = LagomConfig("lagom_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            config.ready()
            assert mock_init.call_args[1]["backend"] == "lagom"

    def test_extra_modules_passed_through(self):
        mod = _make_fake_app_module("extra_app")
        extra = [lambda binder: None]

        class ExtraConfig(AutowiredAppConfig):
            name = "extra_app"
            autowired_packages = ["pkg"]
            autowired_extra_modules = extra

        config = ExtraConfig("extra_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            config.ready()
            assert mock_init.call_args[1]["extra_modules"] is extra

    def test_exclude_patterns_passed_through(self):
        mod = _make_fake_app_module("exclude_app")
        patterns = {"admin", "management"}

        class ExcludeConfig(AutowiredAppConfig):
            name = "exclude_app"
            autowired_packages = ["pkg"]
            autowired_exclude_patterns = patterns

        config = ExcludeConfig("exclude_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            config.ready()
            assert mock_init.call_args[1]["exclude_patterns"] is patterns

    def test_subclass_with_custom_ready(self):
        mod = _make_fake_app_module("custom_app")
        ready_called = False

        class CustomConfig(AutowiredAppConfig):
            name = "custom_app"
            autowired_packages = ["pkg"]

            def ready(self):
                nonlocal ready_called
                super().ready()
                ready_called = True

        config = CustomConfig("custom_app", mod)

        with mock.patch.object(container, "initialize") as mock_init:
            mock_init.return_value = mock.MagicMock()
            config.ready()
            assert ready_called
            mock_init.assert_called_once()
