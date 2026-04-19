# Scopes

| Scope | Behavior | When to use | Backend caveats |
| --- | --- | --- | --- |
| `Scope.SINGLETON` | One instance per container lifetime | Default for all stateless services. | Supported everywhere. |
| `Scope.TRANSIENT` | New instance on every `container.get()` | Stateful factories, one-shot builders. | `wireup` requires an explicit scope to resolve transient injectables from the root — use with care. |
| `Scope.THREAD` | One instance per thread | Request-scoped state in threaded WSGI. | `injector` only. `lagom` / `wireup` / `dishka` fall back to `SINGLETON`. |

## SINGLETON

The default. Use for stateless service classes, repositories, and any
infrastructure you want to share across the whole app.

```python
@injectable(scope=Scope.SINGLETON)
class AuthService: ...
```

## TRANSIENT

A new instance every time. Use for short-lived, stateful collaborators where
sharing would cause interference.

```python
@injectable(scope=Scope.TRANSIENT)
class RequestBuilder:
    def __init__(self) -> None:
        self._headers: dict[str, str] = {}
```

## THREAD

One instance per thread. Works only with the `injector` backend — `lagom`, `wireup`,
and `dishka` don't model thread-locality. Handy for threaded WSGI servers where
each request runs on a dedicated thread.

```python
@injectable(scope=Scope.THREAD)
class UnitOfWork: ...
```

!!! warning "Async servers"
    `Scope.THREAD` is meaningless on asyncio-based servers like FastAPI. All
    coroutines typically run on a single thread. Use `Scope.TRANSIENT` and rely
    on framework-level request scoping (FastAPI's `Depends`, for example).
