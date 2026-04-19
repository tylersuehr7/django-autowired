"""Domain port — abstract greeter interface."""

from abc import ABC, abstractmethod


class IGreeter(ABC):
    """A greeter produces a greeting string for a given name."""

    @abstractmethod
    def greet(self, name: str) -> str: ...
