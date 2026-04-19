# Flask integration

## Installation

```bash
pip install "django-autowired[flask,injector]"
```

## Direct init

```python
from flask import Flask
from django_autowired.integrations.flask import Autowired

app = Flask(__name__)
Autowired(app, packages=["myapp.services"], backend="injector")
```

## Application factory pattern

```python
from flask import Flask
from django_autowired.integrations.flask import Autowired

autowired = Autowired(packages=["myapp.services"])

def create_app() -> Flask:
    app = Flask(__name__)
    autowired.init_app(app)
    return app
```

**Args passed to `init_app()` take precedence** over constructor args:

```python
aw = Autowired(packages=["wrong"], backend="lagom")
aw.init_app(app, packages=["myapp"], backend="injector")   # these win
```

## Resolving dependencies in route handlers

Use `inject_dep(cls)`:

```python
from flask import Flask
from django_autowired.integrations.flask import inject_dep
from myapp.services.greeter import GreetingService

@app.route("/greet/<name>")
def greet(name: str):
    svc = inject_dep(GreetingService)
    return svc.greet(name)
```

## Full example

```python
# app.py
from abc import ABC, abstractmethod
from flask import Flask
from django_autowired import injectable
from django_autowired.integrations.flask import Autowired, inject_dep


class IGreeter(ABC):
    @abstractmethod
    def greet(self, name: str) -> str: ...


@injectable(bind_to=IGreeter)
class FriendlyGreeter(IGreeter):
    def greet(self, name: str) -> str:
        return f"hi, {name}!"


app = Flask(__name__)
Autowired(app, packages=["__main__"], backend="injector")


@app.route("/greet/<name>")
def greet(name: str):
    return {"message": inject_dep(IGreeter).greet(name)}


if __name__ == "__main__":
    app.run()
```
