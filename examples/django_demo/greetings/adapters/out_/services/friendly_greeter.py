"""Greeter service — the port implementation you actually call into."""

from django_autowired import injectable

from greetings.domain.ports.services.greeter import IGreeter
from greetings.domain.ports.services.name_formatter import INameFormatter


@injectable(bind_to=IGreeter)
class FriendlyGreeter(IGreeter):
    """Friendly greeter that relies on a name formatter for normalization."""

    def __init__(self, formatter: INameFormatter) -> None:
        self._formatter = formatter

    def greet(self, name: str) -> str:
        pretty = self._formatter.format(name)
        return f"hello, {pretty}! welcome to django-autowired."
