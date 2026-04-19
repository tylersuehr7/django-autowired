# wireup backend

Wraps [`wireup`](https://github.com/maldoinc/wireup).

## Installation

```bash
pip install "django-autowired[wireup]"
```

## Scope mapping

| `Scope` | wireup lifetime |
| --- | --- |
| `SINGLETON` | `singleton` |
| `TRANSIENT` | `transient` (requires an explicit scope to resolve — see below) |
| `THREAD` | **Falls back to `SINGLETON`** |

## Caveats

- Wireup's root container cannot resolve `transient` injectables without
  explicit scope entry. If you register a class as `TRANSIENT`, you'll need
  to `enter_scope()` on the raw container to resolve it.
- `Scope.THREAD` is silently mapped to `SINGLETON` because wireup has no
  thread-scope concept.

## Overrides

Wireup's runtime override API is context-manager-based (temporary), so the
adapter stores persistent overrides in a local dict and checks them in
`get()` before delegating.

```python
container.override({IGreeter: FakeGreeter()})
```

## Raw access

```python
be = container.get_backend_instance()
raw = be.raw()   # wireup.SyncContainer
```
