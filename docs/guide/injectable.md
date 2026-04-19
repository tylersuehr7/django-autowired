# `@injectable`

The `@injectable` decorator is the only user-facing touchpoint for registering
a class with the container.

## Signature

```python
from django_autowired import injectable, Scope

@injectable(scope: Scope = Scope.SINGLETON, bind_to: type | None = None)
```

The decorator registers the class in the thread-safe global registry and returns
the original class unchanged.

## Concrete class binding

The simplest form — resolve by the class itself:

```python
from django_autowired import injectable

@injectable()
class EmailService:
    def send(self, to: str) -> None:
        ...
```

```python
container.get(EmailService)   # returns an EmailService instance
```

## Interface binding with `bind_to`

Use `bind_to` when you want to resolve by an interface (ABC) rather than the concrete type.

```python
from abc import ABC, abstractmethod
from django_autowired import injectable

class IUserRepository(ABC):
    @abstractmethod
    def find(self, user_id: str) -> User: ...

@injectable(bind_to=IUserRepository)
class SqlUserRepository(IUserRepository):
    def find(self, user_id: str) -> User:
        ...
```

```python
container.get(IUserRepository)    # returns a SqlUserRepository
```

## Scope selection

```python
@injectable(scope=Scope.SINGLETON)   # one per container (default)
@injectable(scope=Scope.TRANSIENT)   # fresh instance per resolution
@injectable(scope=Scope.THREAD)      # one per thread (injector only)
```

See [Scopes](scopes.md) for the full reference.

## `@inject` with the `injector` backend

The `injector` backend auto-applies `@inject` to constructors with type-annotated
parameters, so **you don't have to decorate `__init__`**:

```python
@injectable()
class EmailService:
    def __init__(self, smtp: SmtpClient) -> None:  # auto-injected
        self.smtp = smtp
```

If you prefer explicit decoration, it still works:

```python
import injector

@injectable()
class EmailService:
    @injector.inject
    def __init__(self, smtp: SmtpClient) -> None:
        self.smtp = smtp
```

## The `bind_to` convention

> **Rule:** every class in `adapters/out_/` (or equivalent) that implements a
> domain port **must** use `bind_to=`.

This keeps domain code free of adapter-specific types and makes swapping
implementations a trivial config change.

```python
# src/myapp/domain/ports.py
class IPaymentGateway(ABC): ...

# src/myapp/adapters/out_/stripe.py
@injectable(bind_to=IPaymentGateway)
class StripePaymentGateway(IPaymentGateway): ...
```

## Common mistakes

**Decorating a function.**
`@injectable` only works on classes. For function factories, use the backend's
native mechanism (e.g., `injector.Module`).

**Missing type annotations on `__init__`.**
The backends rely on type hints. Without them, resolution fails loudly:

```python
@injectable()
class Broken:
    def __init__(self, smtp) -> None:   # no annotation → UnresolvableTypeError
        self.smtp = smtp
```

**Two implementations for the same `bind_to`.**
Raises `DuplicateBindingError` at boot. Use `extra_modules` or env-conditional
registration instead of two `@injectable(bind_to=IFoo)` decorators.

**Calling `container.get()` inside a domain class.**
That's the service-locator anti-pattern. Always inject through the constructor.
