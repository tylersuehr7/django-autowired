# django-autowired demo project

A minimal but realistic Django application that shows off `django-autowired`
in a **ports-and-adapters** (hexagonal) architecture.

## What's inside

```
examples/django_demo/
├── manage.py
├── project/                                    # Django settings package
│   ├── settings.py
│   └── urls.py
└── greetings/
    ├── apps.py                                 # AutowiredAppConfig subclass
    ├── urls.py
    ├── views.py                                # Resolves IGreeter at request boundary
    ├── tests.py                                # Three testing patterns
    ├── domain/                                 # pure, no framework imports
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

The layout enforces a clean dependency flow: **domain → nothing**,
**adapters → domain**, **views → domain (for resolution only)**. Domain code
never imports from `adapters/`.

## Run it

From `examples/django_demo/`:

```bash
# Set up the environment (uses the local django-autowired via path dependency)
uv sync

# Apply Django's built-in migrations
uv run python manage.py migrate

# Start the dev server
uv run python manage.py runserver
```

Visit <http://127.0.0.1:8000/greet/ada/>:

```json
{"message": "hello, Ada! welcome to django-autowired."}
```

## Run the tests

```bash
uv run pytest
```

Three tests pass, each showing a different testing strategy:

1. **`test_pure_unit_no_container`** — no container; constructor-injected mocks.
2. **`test_full_wiring`** — real autowiring via the `autowired_container`
   fixture and markers.
3. **`test_override_with_fake_formatter`** — real wiring with a selective
   override of one port.

## Inspect the DI graph

```bash
uv run python -m django_autowired inspect greetings.adapters.out_
```

```
INTERFACE                                              IMPLEMENTATION                                                           SCOPE      KIND       SOURCE
-----------------------------------------------------  -----------------------------------------------------------------------  ---------  ---------  ---------------------------------------------------
greetings.domain.ports.services.greeter.IGreeter       greetings.adapters.out_.services.friendly_greeter.FriendlyGreeter        singleton  interface  greetings.adapters.out_.services.friendly_greeter
greetings.domain.ports.services.name_formatter.INameFormatter  greetings.adapters.out_.services.title_case_name_formatter.TitleCaseNameFormatter  singleton  interface  greetings.adapters.out_.services.title_case_name_formatter
```

Try the tree / mermaid formats too:

```bash
uv run python -m django_autowired inspect greetings.adapters.out_ --format tree
uv run python -m django_autowired inspect greetings.adapters.out_ --format mermaid
```

## Why scan only `greetings.adapters.out_`?

Because that's the **only** place `@injectable` classes live. The domain is
100% abstract — ports are ABCs with no implementation. Adapters implement
them and are the right layer to wire up. This keeps scanning fast and makes
the DI boundary explicit.

## What to take away

- **No `Module` subclass.** No `binder.bind()`. The only DI glue is
  `GreetingsConfig.autowired_packages`.
- **Domain depends on ports, not adapters.** `FriendlyGreeter` takes
  `INameFormatter`, not `TitleCaseNameFormatter`.
- **Every outbound adapter uses `bind_to=`.** This is enforced by convention;
  it's how callers stay decoupled from adapter types.
- **Swapping implementations is one line.** Change the `bind_to=` target
  or override it in tests.
- **Views resolve at the boundary.** `container.get(IGreeter)` only appears
  in `views.py`, never in domain code.
