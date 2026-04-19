"""Flask demo entry point.

Uses the application-factory pattern and the ``Autowired`` Flask extension
to scan ``greetings.adapters.out_`` at startup.
"""

from flask import Flask

from django_autowired.integrations.flask import Autowired
from greetings.routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    Autowired(app, packages=["greetings.adapters.out_"], backend="injector")
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
