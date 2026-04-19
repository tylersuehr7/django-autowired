# lagom backend

Wraps [`lagom`](https://github.com/meadsteve/lagom).

## Installation

```bash
pip install "django-autowired[lagom]"
```

## Scope mapping

| `Scope` | Behavior |
| --- | --- |
| `SINGLETON` | Uses `lagom.Singleton` wrapper |
| `TRANSIENT` | New instance each resolution |
| `THREAD` | Falls back to `TRANSIENT` (lagom has no thread scope) |

## `@inject` is not used

Lagom auto-resolves concrete classes from type hints — you don't need to
decorate `__init__`. Only `bind_to` registrations need explicit definition.

```python
@injectable()
class EmailService:
    def __init__(self, smtp: SmtpClient) -> None:
        self.smtp = smtp
```

## Overrides

Lagom raises `DuplicateDefinition` on re-binding, so the adapter stores
overrides in a per-backend dict and consults it before delegating to the
container.

```python
container.override({IGreeter: FakeGreeter()})
```

## Raw access

```python
be = container.get_backend_instance()
raw: lagom.Container = be.raw()
```
