# Component scanning

The scanner recursively imports every submodule under the packages you list
in `autowired_packages`, triggering the side effects of every `@injectable`
decorator it encounters.

## What gets scanned

Given `autowired_packages = ["myapp.services"]`, every submodule under
`myapp.services.*` gets imported — including nested packages.

## What gets skipped

These name segments are **always** skipped, regardless of configuration:

- `migrations` — Django migration files
- `tests`, `test` — test packages
- `conftest` — pytest configuration
- `factories` — factory_boy / model factories
- `fixtures` — test fixtures

## Custom exclusions

`exclude_patterns` **adds to** the built-in list — it doesn't replace it:

```python
class MyAppConfig(AutowiredAppConfig):
    name = "myapp"
    autowired_packages = ["myapp"]
    autowired_exclude_patterns = {"generated", "legacy"}
```

Now `myapp.generated.*` and `myapp.legacy.*` are also skipped.

## Error handling

| Failure | Log level | Effect |
| --- | --- | --- |
| A root package can't be imported | `ERROR` | That package is skipped entirely. Others continue. |
| A single submodule fails to import | `WARNING` | Only that submodule is skipped. Scanning continues. |
| `@injectable` raises during import | `ERROR` | Aborts — registration errors are real bugs. |

The first two guarantee a half-installed optional dependency never prevents boot.

## Idempotency

Calling `scan_packages(...)` twice is safe — duplicate registrations of the
same class to the same interface are silently idempotent. Only a *conflicting*
registration (two different classes for the same `bind_to`) raises.

## Package structure recommendation

```
myapp/
├── services/
│   ├── __init__.py
│   ├── greeter.py           # @injectable()
│   └── email/
│       └── smtp.py          # @injectable(bind_to=IEmailClient)
├── adapters/
│   └── out_/
│       └── sql_user_repo.py # @injectable(bind_to=IUserRepository)
└── apps.py                  # autowired_packages = ["myapp.services", "myapp.adapters"]
```

List each branch you want scanned explicitly — this keeps scanning fast and
predictable in large apps.
