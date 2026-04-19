import pytest

from django_autowired import container
from django_autowired.registry import clear_registry


@pytest.fixture(autouse=True)
def isolate_container():
    clear_registry()
    container.reset()
    yield
    container.reset()
    clear_registry()


def pytest_configure(config):
    config.addinivalue_line("markers", "autowired_packages: packages to scan")
    config.addinivalue_line("markers", "autowired_backend: backend name")
