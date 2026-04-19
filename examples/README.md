# django-autowired examples

Three minimal-but-realistic demo apps — one per supported framework —
showing the same ports-and-adapters feature wired three different ways.
The **domain and adapter code is byte-for-byte identical** across all
three. Only the framework-boundary wiring changes.

## Demos

| Demo | Framework | Entry point | Route | Test client |
| --- | --- | --- | --- | --- |
| [django_demo/](django_demo/) | Django 5.x | `AutowiredAppConfig.ready()` | `container.get(IGreeter)` in view | `django.test.Client` |
| [fastapi_demo/](fastapi_demo/) | FastAPI | `autowired_lifespan` context manager | `Depends(Provide(IGreeter))` | `fastapi.testclient.TestClient` |
| [flask_demo/](flask_demo/) | Flask | `Autowired(app, packages=[...])` | `inject_dep(IGreeter)` | `app.test_client()` |

## What they all share

- Hexagonal layout: `greetings/domain/ports/...` + `greetings/adapters/out_/...`
- Two ports (`IGreeter`, `INameFormatter`) and two adapters (`FriendlyGreeter`,
  `TitleCaseNameFormatter`)
- Only `greetings.adapters.out_` needs scanning — domain is abstract-only
- Three testing patterns: pure unit, full end-to-end, partial override

## Running a demo

Each demo is a standalone `uv` project that pulls in the local
`django-autowired` via a path dependency. From the demo directory:

```bash
uv sync
uv run pytest                 # 3 tests pass
uv run python <entrypoint>    # manage.py / main.py / app.py
```

## Inspect the DI graph

The `inspect` CLI works the same way in every demo — it doesn't care about
the framework:

```bash
uv run python -m django_autowired inspect greetings.adapters.out_ --format tree
```

## Which framework should you try first?

- **New to the library?** Start with `django_demo/`. The documentation
  treats Django as the priority integration.
- **Building an API?** `fastapi_demo/` shows `Depends(Provide(...))` and
  the async lifespan pattern.
- **Factory-pattern Flask app?** `flask_demo/` uses `create_app()` with the
  `Autowired` extension's `init_app()` flow.
