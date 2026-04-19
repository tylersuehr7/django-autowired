# dishka backend

Wraps [`dishka`](https://github.com/reagento/dishka).

## Installation

```bash
pip install "django-autowired[dishka]"
```

## Scope mapping

| `Scope` | dishka scope | Caching |
| --- | --- | --- |
| `SINGLETON` | `DishkaScope.APP` | cached |
| `TRANSIENT` | `DishkaScope.APP` | uncached (`cache=False`) |
| `THREAD` | `DishkaScope.APP` | cached |

Because dishka's top-level container is APP-scoped, all three map to `APP`.
`TRANSIENT` is expressed via `cache=False` on the provide.

## How it works

The adapter dynamically synthesizes a `Provider` subclass at boot time,
wiring one factory per registration.

## Overrides

Dishka containers are immutable once built, so `override()` closes the
current container and rebuilds with a second `Provider` layered on top
(using `override=True` on the overriding factories).

```python
container.override({IGreeter: FakeGreeter})
```

## Raw access

```python
be = container.get_backend_instance()
raw = be.raw()
```
