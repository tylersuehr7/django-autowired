# Container reference

All lifecycle functions live at `django_autowired.container`.

## `initialize`

```python
from django_autowired import container

container.initialize(
    packages=["myapp.services", "myapp.adapters"],
    backend="injector",           # or "lagom", "wireup", "dishka"
    extra_modules=None,           # backend-specific modules
    exclude_patterns=None,        # additional scan skips
    allow_override=False,         # allow re-initialization
)
```

Scans the packages, builds the backend container, and stores the backend
globally. Raises `ContainerAlreadyInitializedError` if called twice without
`reset()` and `allow_override=False`.

Returns the `AbstractBackend` instance.

## `get`

```python
svc = container.get(MyService)
```

Resolves an instance of `MyService` from the backend. Raises
`ContainerNotInitializedError` if the container hasn't been built yet,
or `UnresolvableTypeError` if the type is unregistered.

## `get_backend_instance`

```python
be = container.get_backend_instance()
be.raw()   # access the native backend container
```

Returns the current backend. Useful when you need a backend-specific feature
(e.g. `injector.create_child()`).

## `override`

```python
container.override({IGreeter: FakeGreeter})
```

Replaces a binding in the current container. The exact semantics depend on the
backend — see the backend-specific docs. **Intended for tests**; prefer
`extra_modules` at boot for production environment differences.

## `reset`

```python
container.reset()
```

Tears down the backend and clears the registry. Only use in tests. In
production, the container is built once at boot and lives for the process
lifetime.

## `is_initialized`

```python
if container.is_initialized():
    ...
```

Returns `True` after a successful `initialize()`, `False` after `reset()`.
