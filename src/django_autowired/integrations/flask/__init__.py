"""Flask integration for django-autowired."""

from django_autowired.integrations.flask.extension import Autowired, inject_dep

__all__ = ["Autowired", "inject_dep"]
