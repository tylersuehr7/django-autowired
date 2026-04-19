# injector backend

The default and most complete backend. Wraps [`injector`](https://github.com/python-injector/injector).

## Installation

```bash
pip install "django-autowired[injector]"
```

## Scope mapping

| `Scope` | injector equivalent |
| --- | --- |
| `SINGLETON` | `injector.singleton` |
| `TRANSIENT` | `injector.noscope` |
| `THREAD` | `injector.threadlocal` |

All three are first-class — no limitations.

## Do I need `@inject`?

**No.** The backend auto-applies `@injector.inject` to any constructor with
fully type-annotated parameters. So this works:

```python
@injectable()
class EmailService:
    def __init__(self, smtp: SmtpClient) -> None:
        self.smtp = smtp
```

If you want explicit decoration, it's also fine:

```python
import injector

@injectable()
class EmailService:
    @injector.inject
    def __init__(self, smtp: SmtpClient) -> None:
        self.smtp = smtp
```

## Full example

```python
from abc import ABC, abstractmethod
from django_autowired import injectable, container, Scope
from django_autowired.integrations.django import AutowiredAppConfig

class IUserRepo(ABC):
    @abstractmethod
    def find(self, uid: str) -> User: ...

@injectable(bind_to=IUserRepo)
class SqlUserRepo(IUserRepo):
    def __init__(self, db: Database) -> None:
        self._db = db
    def find(self, uid: str) -> User:
        ...

@injectable()
class Database: ...

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp"]
    autowired_backend = "injector"

# Later:
repo = container.get(IUserRepo)
repo.find("abc")
```

## Child injectors

Need a request-scoped child container? Use the backend's `create_child()`:

```python
from django_autowired import container

be = container.get_backend_instance()
child = be.create_child([my_request_module])
svc = child.get(RequestScopedThing)
```

## Override

```python
container.override({IUserRepo: FakeUserRepo})
```

Internally this builds a child injector layered on top of the original —
calls to `get()` on the current container reflect the override.

## Raw access

```python
be = container.get_backend_instance()
inj: injector.Injector = be.raw()
```

Reach for this only when you need an `injector`-specific feature the adapter
doesn't expose.
