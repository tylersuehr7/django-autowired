# Extra modules

Not everything can be `@injectable`. Config values, SDK clients from third-party
libraries, environment-specific bindings — those live in `extra_modules`.

## injector backend

Any callable that accepts an `injector.Binder`, or an `injector.Module` subclass.

```python
# myapp/app_modules.py
import injector
from django.conf import settings
from stripe import StripeClient
from myapp.ports import IPaymentGateway, IDatabase

class AppModule(injector.Module):
    def configure(self, binder: injector.Binder) -> None:
        # Concrete SDK client
        binder.bind(
            StripeClient,
            to=StripeClient(api_key=settings.STRIPE_API_KEY),
            scope=injector.singleton,
        )
        # Config value
        binder.bind(str, to=settings.SECRET_KEY, scope=injector.singleton)
```

Register it:

```python
class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp.services", "myapp.adapters"]
    autowired_extra_modules = [AppModule()]
```

## Environment-specific bindings

The recommended pattern is one concrete `@injectable` per interface, with
`extra_modules` swapping implementations in non-prod environments:

```python
# myapp/apps.py
import os
from myapp.adapters.fakes import InMemoryPaymentGateway

extra = []
if os.environ.get("USE_FAKES"):
    def _fakes_module(binder):
        binder.bind(IPaymentGateway, to=InMemoryPaymentGateway)
    extra = [_fakes_module]

class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp"]
    autowired_extra_modules = extra
```

This keeps the code **one concrete per interface** while still giving you
per-environment control.
