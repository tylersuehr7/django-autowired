"""FastAPI demo entry point.

Wires up ``autowired_lifespan`` to scan ``greetings.adapters.out_`` at startup.
"""

from functools import partial

from fastapi import FastAPI

from django_autowired.integrations.fastapi import autowired_lifespan
from greetings.routes import router

app = FastAPI(
    title="django-autowired FastAPI demo",
    lifespan=partial(
        autowired_lifespan,
        packages=["greetings.adapters.out_"],
        backend="injector",
    ),
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
