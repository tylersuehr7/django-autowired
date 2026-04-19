"""Scope enum for controlling instance lifecycle."""

from enum import StrEnum


class Scope(StrEnum):
    """Controls how often a new instance is created.

    Attributes:
        SINGLETON: One instance per container lifetime (default).
        TRANSIENT: New instance on every resolution.
        THREAD: One instance per thread (useful for request-scoped objects in threaded WSGI).
    """

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    THREAD = "thread"
