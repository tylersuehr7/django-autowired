# Testing

`django-autowired` ships with three testing strategies, from pure to
full-integration.

## 1. Pure unit tests (no container)

For testing a single class, don't involve the container. Pass mocks directly
into the constructor:

```python
from myapp.services.order_service import OrderService

def test_places_order():
    svc = OrderService(
        payment_gateway=FakePaymentGateway(),
        inventory=FakeInventory(),
    )
    result = svc.place("SKU-123")
    assert result.status == "confirmed"
```

This is the **fastest**, **most isolated** style. Prefer it for domain logic.

## 2. Integration tests with `autowired_container`

When you need the real wiring, use the pytest fixture + markers:

```python
import pytest
from django_autowired import container
from myapp.services.order_service import OrderService

@pytest.mark.autowired_packages(["myapp.services", "myapp.adapters"])
@pytest.mark.autowired_backend("injector")
def test_full_wiring(autowired_container):
    svc = container.get(OrderService)
    assert svc is not None
```

The fixture initializes the container from your markers, yields the backend,
and resets on teardown.

## 3. Partial integration with `build_container`

When you want real wiring plus selective overrides, use the `build_container`
factory:

```python
def test_order_with_fake_gateway(build_container):
    build_container(
        packages=["myapp.services", "myapp.adapters"],
        overrides={IPaymentGateway: FakePaymentGateway},
    )
    svc = container.get(OrderService)
    ...
```

## Non-pytest: `container_context`

For scripts or doctests:

```python
from django_autowired.testing import container_context

with container_context(
    packages=["myapp.services"],
    overrides={IPaymentGateway: FakePaymentGateway},
):
    svc = container.get(OrderService)
    ...
# container is reset here
```

## `InMemoryOverrideModule` (injector-specific)

When you need overrides applied **during** initialization (not after), wrap
them in an `injector.Module`:

```python
from django_autowired.testing import InMemoryOverrideModule

container.initialize(
    packages=["myapp"],
    extra_modules=[InMemoryOverrideModule({IPaymentGateway: FakePaymentGateway})],
)
```

## Anti-patterns

**Never call `container.get()` inside domain code.**

```python
# BAD
class OrderService:
    def place(self, sku: str):
        gateway = container.get(IPaymentGateway)   # service locator — avoid
        ...

# GOOD
class OrderService:
    def __init__(self, gateway: IPaymentGateway) -> None:
        self._gateway = gateway
```

Catch this in code review: grep for `container.get` in non-framework code.
If you see it outside of `views.py`, `tasks.py`, or similar entrypoints,
it's a smell.
