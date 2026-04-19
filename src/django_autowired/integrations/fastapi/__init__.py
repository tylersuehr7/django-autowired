"""FastAPI integration for django-autowired."""

from django_autowired.integrations.fastapi.lifespan import Provide, autowired_lifespan

__all__ = ["Provide", "autowired_lifespan"]
