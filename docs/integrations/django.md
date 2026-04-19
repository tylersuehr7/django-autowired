# Django integration

The priority integration. If you have to pick one framework to try this library
with, pick Django.

## Installation

```bash
pip install "django-autowired[django,injector]"
```

## Basic usage

**1. Subclass `AutowiredAppConfig`:**

```python
# myapp/apps.py
from django_autowired.integrations.django import AutowiredAppConfig

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp.services", "myapp.adapters"]
    autowired_backend = "injector"    # default
```

**2. Wire it up in `myapp/__init__.py`:**

```python
default_app_config = "myapp.apps.MyAppConfig"
```

**3. Add the app to `INSTALLED_APPS`:**

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "myapp",
]
```

That's it. At Django startup, `ready()` triggers the scan and builds the
container.

## Structuring packages for scanning

```
myapp/
├── __init__.py
├── apps.py
├── services/
│   ├── __init__.py
│   ├── order_service.py        # @injectable()
│   └── email/
│       └── notifier.py         # @injectable()
├── adapters/
│   ├── __init__.py
│   └── out_/
│       ├── __init__.py
│       ├── sql_user_repo.py    # @injectable(bind_to=IUserRepository)
│       └── stripe_gateway.py   # @injectable(bind_to=IPaymentGateway)
├── ports/
│   ├── __init__.py
│   ├── user_repository.py      # IUserRepository(ABC)
│   └── payment_gateway.py      # IPaymentGateway(ABC)
├── migrations/                 # auto-skipped
└── tests/                      # auto-skipped
```

List each branch explicitly:

```python
autowired_packages = ["myapp.services", "myapp.adapters"]
```

## Django-specific bindings (`extra_modules`)

Wrap Django primitives in an `injector.Module`:

```python
import injector
from django.conf import settings
from django.core.cache import cache
from django.db import connection

class DjangoModule(injector.Module):
    def configure(self, binder):
        binder.bind(type(cache), to=cache)
        binder.bind(type(connection), to=connection)
        # Config values
        binder.bind_scalar("secret_key", to=settings.SECRET_KEY)

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp.services", "myapp.adapters"]
    autowired_extra_modules = [DjangoModule()]
```

## Using injected services in views / tasks

```python
# myapp/views.py
from django.http import JsonResponse
from django_autowired import container
from myapp.services.order_service import OrderService

def place_order(request, sku: str):
    svc = container.get(OrderService)
    order = svc.place(sku)
    return JsonResponse({"id": order.id})
```

## Testing with Django's test runner

```python
# myapp/tests/test_order_service.py
import pytest
from django_autowired import container
from myapp.services.order_service import OrderService

@pytest.mark.autowired_packages(["myapp.services", "myapp.adapters"])
@pytest.mark.autowired_backend("injector")
def test_order_service(autowired_container):
    svc = container.get(OrderService)
    assert svc is not None
```

## Compatibility

| Django version | Status |
| --- | --- |
| 5.1 | ✅ |
| 5.0 | ✅ |
| 4.2 LTS | ✅ |

## FAQ

**Why not use Django's built-in signals for this?**

Signals are an *event bus*, not a dependency container. They don't solve
constructor injection, interface binding, or scope management. This library
composes cleanly with signals if you use both.

**Does `AutowiredAppConfig` run on every request?**

No. `ready()` runs once at process start, just like any other `AppConfig.ready()`.

**Can I use this with Django's built-in `injector` patterns (if I already have them)?**

Yes. Put your existing `Module` subclasses into `autowired_extra_modules` and
they'll be merged with the scanned registrations.
