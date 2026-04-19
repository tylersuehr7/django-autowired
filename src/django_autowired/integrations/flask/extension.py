"""Flask extension for django-autowired."""

from __future__ import annotations

from typing import Any, TypeVar

from django_autowired import container
from django_autowired.backends.base import BackendName

T = TypeVar("T")


class Autowired:
    """Flask extension that initializes the autowired container.

    Supports both direct init and the ``init_app()`` factory pattern::

        # Direct
        app = Flask(__name__)
        Autowired(app, packages=["myapp.services"])

        # Factory
        autowired = Autowired(packages=["myapp.services"])
        autowired.init_app(app)

    Args passed to ``init_app()`` take precedence over constructor args.
    """

    def __init__(
        self,
        app: Any | None = None,
        packages: list[str] | None = None,
        backend: BackendName | str = "injector",
        extra_modules: list[Any] | None = None,
        exclude_patterns: set[str] | None = None,
    ) -> None:
        self._packages = packages
        self._backend = backend
        self._extra_modules = extra_modules
        self._exclude_patterns = exclude_patterns

        if app is not None:
            self.init_app(app)

    def init_app(
        self,
        app: Any,
        packages: list[str] | None = None,
        backend: BackendName | str | None = None,
        extra_modules: list[Any] | None = None,
        exclude_patterns: set[str] | None = None,
    ) -> None:
        """Initialize the extension with a Flask app.

        Args passed here take precedence over constructor args.
        """
        resolved_packages = packages or self._packages or []
        resolved_backend = backend or self._backend
        resolved_extra_modules = (
            extra_modules if extra_modules is not None else self._extra_modules
        )
        resolved_exclude = (
            exclude_patterns if exclude_patterns is not None else self._exclude_patterns
        )

        container.initialize(
            packages=resolved_packages,
            backend=resolved_backend,
            extra_modules=resolved_extra_modules,
            exclude_patterns=resolved_exclude,
        )


def inject_dep(cls: type[T]) -> T:
    """Resolve a type from the container. Use in Flask route handlers.

    Example::

        @app.route("/")
        def index():
            svc = inject_dep(MyService)
            return svc.do_work()
    """
    return container.get(cls)
