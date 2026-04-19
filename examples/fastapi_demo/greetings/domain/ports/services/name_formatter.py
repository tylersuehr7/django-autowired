"""Domain port — abstract name formatter interface."""

from abc import ABC, abstractmethod


class INameFormatter(ABC):
    """A name formatter normalizes user input before greeting."""

    @abstractmethod
    def format(self, name: str) -> str: ...
