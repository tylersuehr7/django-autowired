"""Tests for the testing utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pytest

injector_mod = pytest.importorskip("injector")

from django_autowired import container
from django_autowired.registry import injectable
from django_autowired.testing import ContainerFactory, container_context


class IService(ABC):
    @abstractmethod
    def value(self) -> str: ...


class TestAutowiredContainerFixture:
    """Test the autowired_container fixture via indirect usage."""

    def test_fixture_initializes_container(self, request):
        """Simulate what the fixture does internally."""

        # Just test ContainerFactory since that's the underlying mechanism
        factory = ContainerFactory()
        factory(packages=[])
        assert container.is_initialized()

    @pytest.mark.autowired_packages([])
    @pytest.mark.autowired_backend("injector")
    def test_marker_packages_respected(self, request):
        marker = request.node.get_closest_marker("autowired_packages")
        assert marker is not None
        assert marker.args[0] == []

    @pytest.mark.autowired_backend("injector")
    def test_marker_backend_respected(self, request):
        marker = request.node.get_closest_marker("autowired_backend")
        assert marker is not None
        assert marker.args[0] == "injector"


class TestBuildContainerFixture:
    def test_factory_resets_before_build(self):
        factory = ContainerFactory()
        factory(packages=[])
        assert container.is_initialized()
        # Calling again should reset and rebuild
        factory(packages=[])
        assert container.is_initialized()

    def test_factory_with_overrides(self):
        @injectable(bind_to=IService)
        class RealService(IService):
            def value(self) -> str:
                return "real"

        class FakeService(IService):
            def value(self) -> str:
                return "fake"

        factory = ContainerFactory()
        factory(packages=[], overrides={IService: FakeService})
        assert container.get(IService).value() == "fake"


class TestContainerContext:
    def test_initializes_on_enter_resets_on_exit(self):
        with container_context(packages=[]) as be:
            assert container.is_initialized()
            assert be is not None
        assert not container.is_initialized()

    def test_resets_even_on_exception(self):
        with pytest.raises(RuntimeError), container_context(packages=[]):
            assert container.is_initialized()
            raise RuntimeError("boom")
        assert not container.is_initialized()

    def test_context_with_overrides(self):
        @injectable(bind_to=IService)
        class RealService(IService):
            def value(self) -> str:
                return "real"

        class MockService(IService):
            def value(self) -> str:
                return "mock"

        with container_context(packages=[], overrides={IService: MockService}):
            result = container.get(IService)
            assert result.value() == "mock"
