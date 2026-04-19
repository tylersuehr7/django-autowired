# django-autowired FastAPI demo

Mirror of the Django demo, but running on FastAPI. Same
ports-and-adapters layout, same `@injectable` adapters — the only
difference is the wiring code at the framework boundary.

## What's inside

```
examples/fastapi_demo/
├── main.py                                     # FastAPI app + autowired_lifespan
├── conftest.py
├── tests.py
└── greetings/
    ├── routes.py                               # APIRouter; resolves via Depends(Provide(...))
    ├── domain/
    │   └── ports/
    │       └── services/
    │           ├── greeter.py                  # IGreeter (ABC)
    │           └── name_formatter.py           # INameFormatter (ABC)
    └── adapters/
        └── out_/                               # outbound adapters
            └── services/
                ├── friendly_greeter.py         # @injectable(bind_to=IGreeter)
                └── title_case_name_formatter.py  # @injectable(bind_to=INameFormatter)
```

## Run it

From `examples/fastapi_demo/`:

```bash
uv sync
uv run python main.py
# or:
uv run uvicorn main:app --reload
```

Visit <http://127.0.0.1:8000/greet/ada>:

```json
{"message": "hello, Ada! welcome to django-autowired."}
```

Interactive docs: <http://127.0.0.1:8000/docs>

## Run the tests

```bash
uv run pytest
```

Three tests pass, each showing a different testing strategy:

1. **`test_pure_unit_no_container`** — no container; constructor-injected mocks.
2. **`test_end_to_end_real_wiring`** — full app via `TestClient`, hitting the
   HTTP layer with real autowiring.
3. **`test_override_with_fake_formatter`** — real wiring with a selective
   override of one port.

## Inspect the DI graph

```bash
uv run python -m django_autowired inspect greetings.adapters.out_ --format tree
```

## How the wiring compares to Django

| | Django demo | FastAPI demo |
| --- | --- | --- |
| Scan trigger | `AutowiredAppConfig.ready()` | `autowired_lifespan` async CM |
| Resolution in routes | `container.get(IGreeter)` | `Depends(Provide(IGreeter))` |
| Teardown | Never (app lifetime) | `lifespan` exit → `container.reset()` |
| Test client | `django.test.Client` | `fastapi.testclient.TestClient` |

Everything else — `@injectable`, `bind_to=`, the domain/adapter split,
the inspect CLI — is identical across frameworks.
