# django-autowired Flask demo

Mirror of the Django and FastAPI demos, running on Flask. Same
ports-and-adapters layout, same `@injectable` adapters — only the wiring
at the framework boundary differs.

## What's inside

```
examples/flask_demo/
├── app.py                                      # create_app() + Autowired extension
├── conftest.py
├── tests.py
└── greetings/
    ├── routes.py                               # Blueprint; resolves via inject_dep(IGreeter)
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

From `examples/flask_demo/`:

```bash
uv sync
uv run python app.py
# or with Flask's factory auto-detection:
uv run flask --app "app:create_app" run
```

Visit <http://127.0.0.1:5000/greet/ada/>:

```json
{"message": "hello, Ada! welcome to django-autowired."}
```

## Run the tests

```bash
uv run pytest
```

Three tests pass, each showing a different testing strategy:

1. **`test_pure_unit_no_container`** — no container; constructor-injected mocks.
2. **`test_end_to_end_real_wiring`** — full app via Flask's test client,
   hitting the HTTP layer with real autowiring.
3. **`test_override_with_fake_formatter`** — real wiring with a selective
   override of one port.

## Inspect the DI graph

```bash
uv run python -m django_autowired inspect greetings.adapters.out_ --format tree
```

## How the wiring compares to Django / FastAPI

| | Django | FastAPI | Flask |
| --- | --- | --- | --- |
| Scan trigger | `AutowiredAppConfig.ready()` | `autowired_lifespan` CM | `Autowired(app, packages=...)` |
| Resolution in routes | `container.get(IGreeter)` | `Depends(Provide(IGreeter))` | `inject_dep(IGreeter)` |
| Teardown | Never (app lifetime) | `lifespan` exit | Never (app lifetime) |
| Test client | `django.test.Client` | `fastapi.testclient.TestClient` | `app.test_client()` |

The domain, ports, and adapters code is **byte-for-byte identical** across
all three demos. Only `app.py` / `main.py` / `apps.py` change.
