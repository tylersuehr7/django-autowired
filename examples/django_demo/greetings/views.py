"""Demo views — resolve ports from the container at the request boundary."""

from django.http import HttpRequest, JsonResponse

from django_autowired import container
from greetings.domain.ports.services.greeter import IGreeter


def greet(request: HttpRequest, name: str) -> JsonResponse:
    """Resolve the greeter from the container and return a JSON greeting."""
    greeter = container.get(IGreeter)
    return JsonResponse({"message": greeter.greet(name)})
