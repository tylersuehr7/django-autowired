# Build `django-autowired` — Autowiring DI Library for Python

## Mission

Build a production-ready, open source Python library called `django-autowired` that brings
Spring Boot-style `@injectable` autowiring to Python. The library wraps existing DI backends
(injector, lagom, wireup, dishka) with a unified decorator-driven API and zero manual wiring.

---

## Core Design Principles

1. **No hard dependencies.** The core library installs nothing. Every backend and framework
   integration is an optional extra.
2. **Backend-agnostic core.** The `@injectable` decorator, scanner, registry, and container
   are fully decoupled from any specific DI library.
3. **`injector` is the priority backend.** It must be the most complete, best-tested, and
   the default when no backend is specified.
4. **Django is the priority integration.** It must be the most complete, best-tested, and
   the most prominent in documentation. But Django must not be a required dependency.
5. **Spring Boot ergonomics.** No manual module files, no manual binder.bind() calls. A
   developer annotates a class with `@injectable` and the framework handles the rest.
6. **Fail loudly at boot, never silently at runtime.** Duplicate bindings, missing packages,
   and unresolvable types all raise typed, actionable exceptions at initialization time.

---

## Project Structure

```
django-autowired/
├── src/
│   └── django_autowired/
│       ├── __init__.py              # Public API surface
│       ├── scopes.py                # Scope enum (SINGLETON, TRANSIENT, THREAD)
│       ├── exceptions.py            # All typed exceptions
│       ├── registry.py              # @injectable decorator + thread-safe registration store
│       ├── scanner.py               # Recursive package importer (component scan)
│       ├── container.py             # Global container lifecycle
│       ├── testing.py               # pytest fixtures + context manager helpers
│       ├── backends/
│       │   ├── __init__.py          # get_backend() factory + BackendName type
│       │   ├── base.py              # AbstractBackend ABC
│       │   ├── injector_.py         # injector backend (priority)
│       │   ├── lagom_.py            # lagom backend
│       │   ├── wireup_.py           # wireup backend
│       │   └── dishka_.py           # dishka backend
│       └── integrations/
│           ├── django/
│           │   ├── __init__.py
│           │   └── apps.py          # AutowiredAppConfig base class
│           ├── fastapi/
│           │   ├── __init__.py
│           │   └── lifespan.py      # autowired_lifespan + Provide
│           └── flask/
│               ├── __init__.py
│               └── extension.py     # Autowired extension + inject_dep
├── tests/
│   ├── conftest.py                  # Shared fixtures + pytest markers
│   ├── test_registry.py             # Registry and @injectable decorator tests
│   ├── test_scanner.py              # Scanner / component scan tests
│   ├── test_container.py            # Container lifecycle tests
│   ├── test_scopes.py               # Scope behavior tests across backends
│   ├── test_exceptions.py           # Exception type and message tests
│   ├── test_testing_utils.py        # Tests for the testing fixtures themselves
│   ├── backends/
│   │   ├── conftest.py
│   │   ├── test_injector.py         # injector backend tests (most thorough)
│   │   ├── test_lagom.py            # lagom backend tests
│   │   ├── test_wireup.py           # wireup backend tests
│   │   └── test_dishka.py           # dishka backend tests
│   └── integrations/
│       ├── test_django.py           # Django AppConfig integration tests
│       ├── test_fastapi.py          # FastAPI lifespan + Provide tests
│       └── test_flask.py            # Flask extension tests
├── docs/
│   ├── index.md                     # Overview, installation, quickstart
│   ├── guide/
│   │   ├── injectable.md            # @injectable decorator in depth
│   │   ├── scopes.md                # Scope reference
│   │   ├── scanning.md              # Component scanning + exclude patterns
│   │   ├── container.md             # Container lifecycle
│   │   ├── extra_modules.md         # Manual bindings for config/third-party
│   │   └── testing.md               # Testing guide with examples
│   ├── backends/
│   │   ├── injector.md              # injector backend guide
│   │   ├── lagom.md                 # lagom backend guide
│   │   ├── wireup.md                # wireup backend guide
│   │   └── dishka.md                # dishka backend guide
│   ├── integrations/
│   │   ├── django.md                # Django integration guide (priority)
│   │   ├── fastapi.md               # FastAPI integration guide
│   │   └── flask.md                 # Flask integration guide
│   └── reference/
│       └── api.md                   # Full API reference
├── mkdocs.yml                       # MkDocs Material config
├── pyproject.toml                   # Full project metadata + optional deps
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                          # MIT
└── README.md
```

---

## Implementation Spec

### `scopes.py`

Define a `Scope(str, Enum)` with three values:
- `SINGLETON` — one instance per container lifetime (default)
- `TRANSIENT` — new instance on every resolution
- `THREAD` — one instance per thread (for request-scoped objects in threaded WSGI)

### `exceptions.py`

Define all exceptions as subclasses of `AutowiredError(Exception)`:
- `ContainerNotInitializedError` — accessed before `initialize()`
- `ContainerAlreadyInitializedError` — `initialize()` called twice without `reset()`
- `DuplicateBindingError(interface, existing_cls, new_cls)` — two classes bind to same interface
- `BackendNotInstalledError(backend_name, package)` — backend package not installed
- `UnresolvableTypeError(cls, reason)` — container cannot satisfy a type

All messages must be human-readable and actionable, explaining what to do to fix the error.

### `registry.py`

- `Registration` — frozen dataclass with `cls`, `scope`, `bind_to`, and a `target` property
  that returns `bind_to` if set, else `cls`.
- `_Registry` — thread-safe class using `threading.Lock()` for all mutations/reads. Detects
  duplicate interface bindings (two different classes → same `bind_to`) and raises
  `DuplicateBindingError`. Idempotent if the exact same class is re-registered.
- `injectable(scope=Scope.SINGLETON, bind_to=None)` — decorator that registers the class and
  returns it unmodified. Must be transparent to callers.
- `get_registry()` — returns the module-level `_Registry` singleton.
- `clear_registry()` — clears all registrations. Tests only.

### `scanner.py`

- `scan_packages(*package_paths, exclude_patterns=None)` — recursively imports all
  sub-modules under each package, triggering `@injectable` side effects.
- Built-in skip segments (not configurable away): `migrations`, `tests`, `test`,
  `conftest`, `factories`, `fixtures`.
- `exclude_patterns` merges with built-ins, not replaces them.
- Import errors in individual sub-modules are logged as `WARNING` and skipped — a single
  broken module must never prevent boot.
- Root package `ImportError`s are logged as `ERROR` and that package is skipped entirely.

### `container.py`

Global functions (module-level, not a class):

```python
def initialize(
    packages: list[str],
    backend: BackendName | AbstractBackend = "injector",
    extra_modules: list[Any] | None = None,
    exclude_patterns: set[str] | None = None,
    allow_override: bool = False,
) -> AbstractBackend: ...

def get(cls: Type[T]) -> T: ...
def get_backend_instance() -> AbstractBackend: ...
def override(bindings: dict[Type, Any]) -> None: ...
def reset() -> None: ...
def is_initialized() -> bool: ...
```

`reset()` must clear both the backend reference AND the registry.

### `backends/base.py`

`AbstractBackend(ABC)` with abstract methods:
- `build(registrations: list[Registration]) -> None`
- `get(cls: Type[T]) -> T`
- `override(bindings: dict[Type, Any]) -> None`
- `name(cls) -> str` (classmethod)

### Backend implementations

Each backend file follows the same pattern:
1. Guard the import with try/except and set `_AVAILABLE = bool`.
2. `__init__` raises `BackendNotInstalledError` if not available.
3. Map `Scope` values to the backend's native scope concept.
4. `build()` registers all `Registration` objects with the native container.
5. `get()` wraps native resolution in `UnresolvableTypeError` on failure.
6. `override()` applies replacement bindings. Backends with immutable containers
   (dishka, wireup) rebuild or layer a new container.
7. Expose a `raw()` method returning the native container for advanced use.

**injector backend specifics:**
- `Scope.SINGLETON` → `injector.singleton`
- `Scope.TRANSIENT` → `injector.noscope`
- `Scope.THREAD` → `injector.threadlocal`
- `extra_modules` are applied by creating a child `Injector` with those modules as parent.
- Expose `create_child(extra_modules)` for request-scoped child containers.

**lagom backend specifics:**
- Lagom resolves concretes automatically from type hints. Only `bind_to` registrations
  need explicit definition. Singletons use lagom's `Singleton` wrapper.
- Document clearly that `@inject` from `injector` is not used/needed.

**wireup backend specifics:**
- Wireup containers are immutable post-build. `override()` stores overrides in a local dict
  and checks them in `get()` before delegating to the container.
- `Scope.THREAD` falls back to `TRANSIENT` — document this limitation.

**dishka backend specifics:**
- Dishka uses provider classes. Dynamically generate a `Provider` subclass with
  `@provide`-decorated factory methods from the registrations list.
- `Scope.SINGLETON` → `DishkaScope.APP`. `TRANSIENT` and `THREAD` → `DishkaScope.REQUEST`.
- `override()` closes the old container and rebuilds with an `OverrideProvider` layered on top.

### `integrations/django/apps.py`

`AutowiredAppConfig(AppConfig)`:
- Class attributes: `autowired_packages`, `autowired_backend="injector"`,
  `autowired_extra_modules=[]`, `autowired_exclude_patterns=set()`.
- `ready()` calls `container.initialize(...)` using the class attributes.
- Warns (not errors) if `autowired_packages` is empty.
- Raises `ImportError` with install instructions if Django is not installed.

### `integrations/fastapi/lifespan.py`

- `autowired_lifespan(app, packages, backend, extra_modules, exclude_patterns)` —
  async context manager. Calls `initialize()` on enter, `reset()` on exit.
- `Provide(cls)` — callable class usable as `Depends(Provide(MyService))`.

### `integrations/flask/extension.py`

- `Autowired` — Flask extension class supporting both direct init and `init_app()` factory
  pattern. Parameters can be passed to constructor or to `init_app()`, with `init_app()`
  args taking precedence.
- `inject_dep(cls)` — resolves from container. Use in route handlers.

### `testing.py`

- `autowired_container` — pytest fixture. Reads `@pytest.mark.autowired_packages([...])` and
  `@pytest.mark.autowired_backend("injector")` markers. Calls `initialize(allow_override=True)`,
  yields the backend, then calls `reset()`.
- `build_container` — pytest fixture yielding a `ContainerFactory` instance. The factory is a
  callable: `factory(packages, overrides, backend, extra_modules)`. Calls `reset()` before each
  build and after the test.
- `container_context(packages, backend, overrides, extra_modules)` — sync context manager for
  non-pytest use.
- `InMemoryOverrideModule(overrides: dict)` — helper that wraps a dict into an
  `injector.Module` for use with `extra_modules`.

### `__init__.py` (public API)

Export exactly:
```python
from .registry import injectable
from .scopes import Scope
from . import container
from .container import get_injector  # alias for container.get_backend_instance()
from .exceptions import (
    AutowiredError,
    ContainerNotInitializedError,
    ContainerAlreadyInitializedError,
    DuplicateBindingError,
    BackendNotInstalledError,
    UnresolvableTypeError,
)
__version__ = "0.1.0"
__all__ = [...]
```

---

## Test Suite Requirements

### General rules for all tests:
- Use `pytest.importorskip("injector")` etc. at the top of each backend test file so tests
  are automatically skipped if the backend is not installed.
- Every test must be fully isolated: the `autouse` fixture in `conftest.py` must call
  `container.reset()` before and after every test.
- No test should depend on execution order.
- Use `abc.ABC` and `@abstractmethod` for all test interfaces — do not use `typing.Protocol`
  for interfaces in tests (avoid runtime_checkable complexity).
- Prefer direct instantiation (no container) for pure unit tests of single classes.

### `tests/conftest.py`

```python
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
```

Register custom markers: `autowired_packages`, `autowired_backend`.

### `tests/test_registry.py` — cover:
- `@injectable()` registers a concrete class (no `bind_to`)
- `@injectable(bind_to=IFoo)` registers with interface binding
- `registration.target` returns `bind_to` when set, else `cls`
- Duplicate binding (two different classes → same interface) raises `DuplicateBindingError`
- Re-registering the exact same class to the same interface is idempotent (no raise)
- `clear_registry()` removes all registrations
- Thread safety: 50 threads simultaneously registering different classes, no data corruption
- `@injectable` returns the original class unchanged (decorator transparency)

### `tests/test_scanner.py` — cover:
- A package containing `@injectable` classes is scanned and they appear in the registry
- `migrations` sub-packages are skipped
- `tests` sub-packages are skipped
- Custom `exclude_patterns` are respected
- A sub-module with an `ImportError` is skipped with a warning, others still scanned
- A root package that doesn't exist logs an error and skips gracefully
- Scan is idempotent (calling twice doesn't double-register)

### `tests/test_container.py` — cover:
- `get()` before `initialize()` raises `ContainerNotInitializedError`
- `initialize()` twice without `reset()` raises `ContainerAlreadyInitializedError`
- `initialize(allow_override=True)` permits re-initialization
- `reset()` then `initialize()` works cleanly
- `is_initialized()` returns correct state before/after init/reset
- `override()` before init raises `ContainerNotInitializedError`
- `get_backend_instance()` returns the backend passed to `initialize()`
- Passing a pre-instantiated backend object (not a string) to `initialize()` works

### `tests/test_scopes.py` — cover (for injector backend):
- `Scope.SINGLETON` → same instance on multiple `get()` calls
- `Scope.TRANSIENT` → different instance on every `get()` call
- `Scope.THREAD` → same instance within a thread, different across threads

### `tests/test_exceptions.py` — cover:
- Each exception has a meaningful `str()` message
- `DuplicateBindingError` message contains all three type names
- `BackendNotInstalledError` message contains install instructions
- `UnresolvableTypeError` message contains the class name

### `tests/backends/test_injector.py` — cover:
- Concrete class resolved without `bind_to`
- Interface resolved to concrete via `bind_to`
- Transitive injection chain (A → B → C all `@injectable`)
- `Scope.SINGLETON` instance reuse
- `Scope.TRANSIENT` fresh instances
- `extra_modules` override a binding
- `override()` replaces a binding
- `raw()` returns an `injector.Injector`
- `create_child()` creates a child injector
- `@inject` constructor annotation works correctly
- Constructor with no `@inject` but type annotations is still resolved
- `UnresolvableTypeError` raised for unregistered type

### `tests/backends/test_lagom.py` — cover:
- Concrete class resolved
- Interface resolved to concrete via `bind_to`
- Singleton scope reuses instance
- Transient scope creates new instances
- `override()` with class replacement
- `override()` with instance replacement
- `raw()` returns a lagom `Container`

### `tests/backends/test_wireup.py` — cover:
- Concrete class resolved
- Interface resolved via `bind_to`
- Singleton scope
- `override()` with class and instance
- `Scope.THREAD` falls back gracefully (no error, just transient behavior)

### `tests/backends/test_dishka.py` — cover:
- Concrete class resolved
- Interface resolved via `bind_to`
- Singleton scope (`DishkaScope.APP`)
- `override()` rebuilds container with replacement
- `raw()` returns a dishka `Container`

### `tests/integrations/test_django.py` — cover:
- `AutowiredAppConfig.ready()` calls `container.initialize()` with correct args
- Empty `autowired_packages` emits a `UserWarning`
- `autowired_backend` attribute is used
- `autowired_extra_modules` attribute is passed through
- `autowired_exclude_patterns` attribute is passed through
- A subclass with a custom `ready()` that calls `super().ready()` works correctly

Use `django.test.utils.setup_test_environment` and mock `AppConfig.ready()` — you do not
need a full Django project, just `DJANGO_SETTINGS_MODULE` set to a minimal settings dict
via `django.conf.settings.configure(...)`.

### `tests/integrations/test_fastapi.py` — cover:
- `autowired_lifespan` initializes container on enter, resets on exit
- `Provide(MyService)` resolves from container when called
- `Provide` works as `Depends(Provide(MyService))` in a TestClient request
- Exception in lifespan body still triggers `reset()` (finally block)

### `tests/integrations/test_flask.py` — cover:
- `Autowired(app, packages=[...])` initializes container
- `Autowired().init_app(app, packages=[...])` factory pattern works
- `init_app()` args take precedence over constructor args
- `inject_dep(MyService)` resolves from container within app context

### `tests/test_testing_utils.py` — cover:
- `autowired_container` fixture initializes and tears down container
- `@pytest.mark.autowired_packages` marker is respected
- `@pytest.mark.autowired_backend` marker is respected
- `build_container` factory resets before each call
- `build_container` with `overrides` applies them
- `container_context` initializes on enter, resets on exit
- `container_context` resets even on exception

---

## Documentation Requirements

### `README.md`

Must include:
1. One-line description
2. Badges: PyPI version, Python versions, license, CI status
3. **Why** section explaining the problem (manual injector.Module wiring at scale)
4. Feature highlights in a compact table or list
5. **Quickstart** — 15 lines of code showing `@injectable`, `AutowiredAppConfig`, done
6. Backend support matrix table (injector ✓ priority, lagom ✓, wireup ✓, dishka ✓)
7. Framework support table (Django ✓ priority, FastAPI ✓, Flask ✓, plain Python ✓)
8. Installation section with all optional extras documented
9. Link to full docs

### `docs/index.md`

Full narrative introduction: the problem, the solution, the philosophy. 
Installation table for all extras. Quickstart with Django (full working example).

### `docs/guide/injectable.md`

- Decorator signature and all parameters explained
- Concrete class binding (no `bind_to`)
- Interface binding (`bind_to=IMyRepository`)
- Scope selection
- `@inject` usage with `injector` backend
- Rule: every class in `adapters/out_/` implementing a domain port MUST use `bind_to=`
- Common mistakes and how to fix them

### `docs/guide/scopes.md`

Reference table of all three scopes with: name, behavior, when to use, backend caveats.
Include note about `Scope.THREAD` not being supported in lagom/wireup/dishka.

### `docs/guide/scanning.md`

How the scanner works, what it skips by default, `exclude_patterns`, how to structure
packages so scanning is predictable. Include note about migration files being auto-skipped.

### `docs/guide/container.md`

Full reference for all container functions with examples for each.

### `docs/guide/extra_modules.md`

How to register things that can't use `@injectable` — config values, third-party SDK
clients, environment-specific overrides. Full example with `injector.Module`.

### `docs/guide/testing.md`

Three testing strategies:
1. Pure unit test (no container, just `MyClass(mock_dep_a, mock_dep_b)`)
2. `autowired_container` fixture for integration tests
3. `build_container` with `overrides` for partial integration tests

Include anti-patterns: never call `container.get()` inside domain code (service locator
anti-pattern). Show how to detect this in code review.

### `docs/backends/*.md`

For each backend: installation, how it maps scopes, any limitations (e.g. wireup/dishka
override caveats), whether `@inject` is needed, full working example.

### `docs/integrations/django.md` (priority — most detailed)

- Installation
- Full `AutowiredAppConfig` example
- How to structure a module for scanning
- `extra_modules` for Django-specific bindings (database, cache, settings values)
- Testing with Django's test runner
- Compatibility table (Django 4.2 LTS, 5.0, 5.1)
- FAQ: "Why not use Django's built-in signals for this?"

### `docs/integrations/fastapi.md`

- `autowired_lifespan` usage
- `Provide` with `Depends`
- Async services (note: use `Scope.TRANSIENT` or ensure thread safety)
- Full working app example

### `docs/integrations/flask.md`

- `Autowired` extension both init styles
- `inject_dep` in route handlers
- Application factory pattern

### `docs/reference/api.md`

Auto-generated from docstrings via `mkdocstrings`.

### `CONTRIBUTING.md`

- Dev setup: `pip install -e ".[dev]"`
- Running tests: `pytest` / `pytest tests/backends/test_injector.py`
- Running all backends: `pytest -m "injector or lagom or wireup or dishka"`
- Linting: `ruff check src tests`
- Type checking: `mypy src`
- Adding a new backend: step-by-step guide
- Adding a new integration: step-by-step guide
- PR checklist

### `CHANGELOG.md`

Follow [Keep a Changelog](https://keepachangelog.com). Start with `[0.1.0] - Unreleased`.

### `mkdocs.yml`

Use MkDocs Material theme with:
- `navigation.tabs`
- `navigation.sections`
- `content.code.copy`
- `pymdownx.highlight` for code blocks
- Dark/light mode toggle

---

## `pyproject.toml` Requirements

```toml
[project]
name = "django-autowired"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []  # NO hard dependencies

[project.optional-dependencies]
injector = ["injector>=0.21"]
lagom    = ["lagom>=2.6"]
wireup   = ["wireup>=0.14"]
dishka   = ["dishka>=0.14"]
django   = ["Django>=4.2"]
fastapi  = ["fastapi>=0.110", "anyio>=4.0"]
flask    = ["Flask>=3.0"]
testing  = ["pytest>=8.0", "pytest-asyncio>=0.23"]
dev      = [
    "django-autowired[injector,lagom,wireup,dishka,django,fastapi,flask,testing]",
    "pytest>=8.0", "pytest-asyncio>=0.23", "pytest-cov>=5.0",
    "mypy>=1.9", "ruff>=0.4",
    "mkdocs>=1.5", "mkdocs-material>=9.5", "mkdocstrings[python]>=0.24",
]
```

---

## `.github/workflows/ci.yml`

Matrix CI across:
- Python versions: `3.10`, `3.11`, `3.12`, `3.13`
- OS: `ubuntu-latest`

Steps:
1. Checkout
2. Set up Python
3. `pip install -e ".[dev]"`
4. `ruff check src tests`
5. `mypy src`
6. `pytest --cov=src/django_autowired --cov-report=xml`
7. Upload coverage to Codecov

---

## Key Conventions to Enforce Throughout

1. **`bind_to` for all port implementations.** Any class implementing an ABC or Protocol
   that lives in an `adapters/out_/` or equivalent directory MUST use `bind_to=`. The docs
   and a CONTRIBUTING checklist item should enforce this.

2. **Never `container.get()` in domain code.** The container is for framework code only.
   Dependency resolution happens via constructor injection. Document this as an anti-pattern.

3. **One concrete class per interface.** If you need environment-specific implementations,
   use `extra_modules` conditioned on an env var, not multiple `@injectable(bind_to=...)`.

4. **`reset()` in tests only.** The container lifecycle is: init once at boot, never reset
   in production. Only tests call `reset()`.

5. **Type annotations required for injection.** All injectable constructors must have fully
   typed `__init__` parameters. The scanner relies on type annotations, not runtime magic.