# django-autowired

> Spring Boot-style `@injectable` autowiring for Python. Any DI backend. Zero manual wiring.

[![PyPI version](https://img.shields.io/pypi/v/django-autowired.svg)](https://pypi.org/project/django-autowired/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-autowired.svg)](https://pypi.org/project/django-autowired/)
[![License](https://img.shields.io/pypi/l/django-autowired.svg)](https://github.com/tylersuehr/django-autowired/blob/main/LICENSE)
[![CI](https://github.com/tylersuehr/django-autowired/actions/workflows/ci.yml/badge.svg)](https://github.com/tylersuehr/django-autowired/actions/workflows/ci.yml)

## Why

In large Django / FastAPI / Flask codebases, hand-rolling `injector.Module` subclasses
with `binder.bind(IRepository, to=SqlRepository)` calls does not scale. It's boilerplate,
it's easy to forget, and every new service becomes a coordination problem.

`django-autowired` brings the Spring Boot ergonomic to Python: decorate a class with
`@injectable`, point an `AppConfig` (or FastAPI lifespan, or Flask extension) at the
packages to scan, and the rest happens at boot.

## Features

| | |
| --- | --- |
| **Zero wiring** | No `Module` subclasses, no `binder.bind()` calls. Just `@injectable`. |
| **Backend-agnostic** | Works with `injector`, `lagom`, `wireup`, or `dishka`. Swap with one line. |
| **Framework-agnostic core** | Django, FastAPI, Flask, or plain Python — all first-class. |
| **Fail loud at boot** | Duplicate bindings, missing backends, and unresolvable types raise typed errors. |
| **Test-friendly** | Pytest fixtures, overrides, and a context manager ship with the library. |
| **Thread-safe registry** | Concurrent registration is safe by construction. |

## Quickstart (Django)

```python
# myapp/apps.py
from django_autowired.integrations.django import AutowiredAppConfig

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp.services", "myapp.adapters"]

# myapp/services.py
from django_autowired import injectable

@injectable()
class GreetingService:
    def greet(self) -> str:
        return "hello"

# myapp/views.py
from django_autowired import container
from myapp.services import GreetingService

def index(request):
    svc = container.get(GreetingService)
    return HttpResponse(svc.greet())
```

That's it. No modules. No binder. No manual wiring.

## Backend support

| Backend  | Status | Priority | Notes |
| -------- | ------ | -------- | ----- |
| `injector` | ✅ | **default** | Most complete. Thread scope supported. |
| `lagom` | ✅ |  | Auto-resolves concretes from type hints. |
| `wireup` | ✅ |  | Thread scope falls back to singleton. |
| `dishka` | ✅ |  | Rebuild-on-override semantics. |

Install the backend you want:

```bash
pip install "django-autowired[injector]"   # default
pip install "django-autowired[lagom]"
pip install "django-autowired[wireup]"
pip install "django-autowired[dishka]"
```

## Framework support

| Framework | Status | Priority |
| --------- | ------ | -------- |
| Django | ✅ | **priority** |
| FastAPI | ✅ | |
| Flask | ✅ | |
| Plain Python | ✅ | |

## Installation

```bash
pip install django-autowired                       # core only (no backend)
pip install "django-autowired[injector]"           # default backend
pip install "django-autowired[django,injector]"    # Django + injector
pip install "django-autowired[fastapi,injector]"   # FastAPI + injector
pip install "django-autowired[flask,injector]"     # Flask + injector
pip install "django-autowired[dev]"                # everything + test/lint/docs
```

Or with `uv`:

```bash
uv add "django-autowired[django,injector]"
```

## Documentation

Full docs at **[tylersuehr7.github.io/django-autowired](https://tylersuehr7.github.io/django-autowired)**.

- [Quickstart](https://tylersuehr7.github.io/django-autowired)
- [`@injectable` guide](https://tylersuehr7.github.io/django-autowired/guide/injectable)
- [Scopes](https://tylersuehr7.github.io/django-autowired/guide/scopes)
- [Django integration](https://tylersuehr7.github.io/django-autowired/integrations/django)
- [FastAPI integration](https://tylersuehr7.github.io/django-autowired/integrations/fastapi)
- [Flask integration](https://tylersuehr7.github.io/django-autowired/integrations/flask)
- [Testing guide](https://tylersuehr7.github.io/django-autowired/guide/testing)

## License

MIT © 2026 Tyler R. Suehr
