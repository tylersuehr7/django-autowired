# django-autowired

> Spring Boot-style `@injectable` autowiring for Python. Any DI backend. Zero manual wiring.

## The problem

In large Python codebases, manual dependency wiring becomes a coordination tax.
Every new service means opening an `injector.Module`, adding a `binder.bind()` call,
remembering the right scope, and reviewing the change. When services implement ABCs
and need to be interchangeable by environment, it gets worse.

## The solution

`django-autowired` treats your package tree like a Spring classpath. Decorate a class,
register the package for scanning, and the DI container wires itself at boot.

## Philosophy

1. **Fail loudly at boot, never silently at runtime.** Duplicate bindings, missing
   backends, and unresolvable types all raise typed exceptions during initialization.
2. **No hard dependencies.** The core library installs nothing. Every backend and
   framework is an optional extra.
3. **One decorator, one registry, any backend.** Switching from `injector` to `lagom`
   is a single-line change.
4. **Django and `injector` are first-class.** They're the default and get the most
   complete, best-tested integration. Every other stack is fully supported.

## Installation

| Extra | Install | Brings in |
| --- | --- | --- |
| *(none)* | `pip install django-autowired` | Core only (no backend) |
| `injector` | `pip install "django-autowired[injector]"` | Default backend |
| `lagom` | `pip install "django-autowired[lagom]"` | Alternative backend |
| `wireup` | `pip install "django-autowired[wireup]"` | Alternative backend |
| `dishka` | `pip install "django-autowired[dishka]"` | Alternative backend |
| `django` | `pip install "django-autowired[django]"` | Django integration |
| `fastapi` | `pip install "django-autowired[fastapi]"` | FastAPI integration |
| `flask` | `pip install "django-autowired[flask]"` | Flask integration |
| `testing` | `pip install "django-autowired[testing]"` | pytest fixtures |

Typical combo:

```bash
pip install "django-autowired[django,injector,testing]"
```

## Quickstart — Django

**1. Declare your services with `@injectable`.**

```python
# myapp/services/greeter.py
from django_autowired import injectable

@injectable()
class GreetingService:
    def greet(self, name: str) -> str:
        return f"hello, {name}"
```

**2. Point your `AppConfig` at the packages to scan.**

```python
# myapp/apps.py
from django_autowired.integrations.django import AutowiredAppConfig

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp.services", "myapp.adapters"]
```

**3. Register the config in `myapp/__init__.py`:**

```python
default_app_config = "myapp.apps.MyAppConfig"
```

**4. Resolve dependencies anywhere.**

```python
# myapp/views.py
from django_autowired import container
from myapp.services.greeter import GreetingService

def hello(request, name: str):
    svc = container.get(GreetingService)
    return HttpResponse(svc.greet(name))
```

That's the whole integration. No `binder.bind()`. No `Module` subclasses.

## Next steps

- **[`@injectable`](guide/injectable.md)** — the decorator in depth
- **[Scopes](guide/scopes.md)** — singleton, transient, thread
- **[Scanning](guide/scanning.md)** — how packages get discovered
- **[Django integration](integrations/django.md)** — the full tour
- **[Testing](guide/testing.md)** — pytest fixtures and overrides
