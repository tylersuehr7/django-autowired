# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

### Added

- `django_autowired.inspect` module with `BindingReport`, `report()`, and
  renderers for `table`, `tree`, `json`, and `mermaid` output.
- `python -m django_autowired inspect` CLI that scans packages and prints
  a report of registered `@injectable` bindings without requiring a running
  container. Supports `--format` and `--exclude`.
- `@injectable` decorator with optional `bind_to` and `scope`.
- `Scope` enum: `SINGLETON`, `TRANSIENT`, `THREAD`.
- Thread-safe `_Registry` that detects duplicate interface bindings at decoration time.
- `scan_packages(*paths, exclude_patterns=...)` with built-in skips for
  `migrations`, `tests`, `test`, `conftest`, `factories`, `fixtures`.
- Global container lifecycle: `initialize`, `get`, `override`, `reset`, `is_initialized`.
- Backend adapters:
  - `InjectorBackend` (priority) — auto-applies `@inject` to annotated constructors.
  - `LagomBackend` — dict-based overrides to work around immutable definitions.
  - `WireupBackend` — `create_sync_container` + `injectable` decorator composition.
    `Scope.THREAD` falls back to `SINGLETON`.
  - `DishkaBackend` — dynamic `Provider` synthesis with rebuild-on-override.
- Integrations:
  - `AutowiredAppConfig` for Django.
  - `autowired_lifespan` + `Provide` for FastAPI.
  - `Autowired` extension + `inject_dep` for Flask.
- Testing utilities: `autowired_container` fixture, `build_container` factory,
  `container_context`, `InMemoryOverrideModule`.
- Typed exceptions: `AutowiredError`, `ContainerNotInitializedError`,
  `ContainerAlreadyInitializedError`, `DuplicateBindingError`,
  `BackendNotInstalledError`, `UnresolvableTypeError`.

[0.1.0]: https://github.com/tylersuehr/django-autowired/releases/tag/v0.1.0
