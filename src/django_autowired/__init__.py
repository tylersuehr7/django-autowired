"""django-autowired — Spring Boot-style @injectable autowiring for Python."""

from django_autowired import container
from django_autowired.exceptions import (
    AutowiredError,
    BackendNotInstalledError,
    ContainerAlreadyInitializedError,
    ContainerNotInitializedError,
    DuplicateBindingError,
    UnresolvableTypeError,
)
from django_autowired.registry import injectable
from django_autowired.scopes import Scope

# Alias for convenient access to the backend instance.
get_injector = container.get_backend_instance

__version__ = "0.1.0"

__all__ = [
    "injectable",
    "Scope",
    "container",
    "get_injector",
    "AutowiredError",
    "ContainerNotInitializedError",
    "ContainerAlreadyInitializedError",
    "DuplicateBindingError",
    "BackendNotInstalledError",
    "UnresolvableTypeError",
]
