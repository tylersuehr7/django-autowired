# FastAPI integration

## Installation

```bash
pip install "django-autowired[fastapi,injector]"
```

## Lifespan setup

Use `autowired_lifespan` as the FastAPI lifespan:

```python
from functools import partial
from fastapi import FastAPI
from django_autowired.integrations.fastapi import autowired_lifespan

app = FastAPI(
    lifespan=partial(
        autowired_lifespan,
        packages=["myapp.services", "myapp.adapters"],
        backend="injector",
    )
)
```

The lifespan initializes the container on startup and resets it on shutdown,
even if startup raises.

## Resolving dependencies in routes

Use `Provide(cls)` with `Depends`:

```python
from fastapi import Depends
from django_autowired.integrations.fastapi import Provide
from myapp.services.greeter import GreetingService

@app.get("/greet/{name}")
async def greet(name: str, svc: GreetingService = Depends(Provide(GreetingService))):
    return {"message": svc.greet(name)}
```

## Async services

FastAPI is an async framework — if your `@injectable` classes hit the event
loop (async DB drivers, `httpx.AsyncClient`, etc.), be explicit about
lifetime:

```python
@injectable(scope=Scope.TRANSIENT)
class UserRepository:
    def __init__(self, db: AsyncDB) -> None:
        self._db = db
```

!!! warning
    `Scope.THREAD` has no meaning on asyncio servers. All coroutines typically
    run on a single thread. Prefer `TRANSIENT` for per-request state.

## Full example

```python
# app.py
from abc import ABC, abstractmethod
from functools import partial
from fastapi import Depends, FastAPI
from django_autowired import injectable
from django_autowired.integrations.fastapi import Provide, autowired_lifespan


class IGreeter(ABC):
    @abstractmethod
    def greet(self, name: str) -> str: ...


@injectable(bind_to=IGreeter)
class FriendlyGreeter(IGreeter):
    def greet(self, name: str) -> str:
        return f"hi, {name}!"


app = FastAPI(
    lifespan=partial(autowired_lifespan, packages=["__main__"], backend="injector")
)


@app.get("/greet/{name}")
async def greet(name: str, svc: IGreeter = Depends(Provide(IGreeter))):
    return {"message": svc.greet(name)}
```
