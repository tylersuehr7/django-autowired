"""AutowiredAppConfig for the greetings app.

This is the only place DI wiring lives. Every class decorated with
``@injectable`` under the listed packages is discovered and wired at boot.
"""

from django_autowired.integrations.django import AutowiredAppConfig


class GreetingsConfig(AutowiredAppConfig):
    name = "greetings"
    autowired_packages = ["greetings.adapters.out_"]
    autowired_backend = "injector"
