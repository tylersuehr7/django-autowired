# Contributing to django-autowired

Thanks for your interest in improving `django-autowired`. This guide covers local
setup, the test layout, and how to add backends or integrations.

## Dev setup

We recommend [`uv`](https://docs.astral.sh/uv/) for dependency and environment
management. The Makefile wraps everything else.

```bash
git clone https://github.com/tylersuehr7/django-autowired
cd django-autowired
make install   # creates .venv, installs all extras
```

Without `uv`:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
make test                  # full suite
make test-injector         # injector backend only
make test-lagom            # lagom backend only
make test-wireup           # wireup backend only
make test-dishka           # dishka backend only

# Or directly:
uv run pytest tests/backends/test_injector.py
uv run pytest tests/ -k "TestScope"
```

Every test must work in isolation — the autouse `isolate_container` fixture in
`tests/conftest.py` resets the registry + container around each test.

## Lint, format, typecheck

```bash
make lint       # ruff check
make format     # ruff format + fix
make typecheck  # mypy
```

## Docs

```bash
make docs         # build site to ./site
make docs-serve   # live-reload at http://localhost:8000
```

## Adding a new backend

1. Create `src/django_autowired/backends/<name>_.py`.
2. Implement `AbstractBackend`:
   - `name()` classmethod returning the short name.
   - `build(registrations, extra_modules)` — configure the native container.
   - `get(cls)` — resolve an instance, wrapping errors in `UnresolvableTypeError`.
   - `override(bindings)` — apply replacement bindings.
   - `raw()` — return the native container.
3. Guard the import with `try/except ImportError` and set `_AVAILABLE = False`
   so `pytest.importorskip` works cleanly.
4. Raise `BackendNotInstalledError` from `__init__` when unavailable.
5. Add a branch to `get_backend()` in `backends/__init__.py`.
6. Add the `Literal` string to `BackendName` in `backends/base.py`.
7. Add an entry to `[project.optional-dependencies]` in `pyproject.toml`.
8. Write `tests/backends/test_<name>.py` mirroring `test_injector.py`.
9. Document scope mapping, override semantics, and any caveats in
   `docs/backends/<name>.md`.

## Adding a new integration

1. Create `src/django_autowired/integrations/<framework>/`.
2. Expose a minimal helper (`AppConfig` subclass, lifespan, extension, etc.).
3. `try/except ImportError` the framework import and raise a clear error.
4. Write `tests/integrations/test_<framework>.py`.
5. Document usage in `docs/integrations/<framework>.md`.

## PR checklist

- [ ] `make test` passes (all backends where applicable)
- [ ] `make lint` clean
- [ ] `make typecheck` clean
- [ ] New public API has docstrings
- [ ] Tests cover new functionality
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Docs updated if behavior or API changed

## Coding conventions

- No hard dependencies in the core. Every backend / framework is an optional extra.
- Any class implementing an ABC in an `adapters/out_/` directory MUST use `bind_to=`.
- Never call `container.get()` inside domain code — use constructor injection.
- `reset()` is for tests only; production code calls `initialize()` once at boot.
- All injectable constructors need fully typed parameters.
