"""Flask blueprint — resolves ports from the container via ``inject_dep``."""

from flask import Blueprint, jsonify

from django_autowired.integrations.flask import inject_dep
from greetings.domain.ports.services.greeter import IGreeter

bp = Blueprint("greetings", __name__)


@bp.route("/greet/<name>/")
def greet(name: str):
    greeter = inject_dep(IGreeter)
    return jsonify({"message": greeter.greet(name)})
