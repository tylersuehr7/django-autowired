"""Title-case name formatter — outbound adapter for ``INameFormatter``."""

from django_autowired import injectable

from greetings.domain.ports.services.name_formatter import INameFormatter


@injectable(bind_to=INameFormatter)
class TitleCaseNameFormatter(INameFormatter):
    """Capitalizes the first letter of each word."""

    def format(self, name: str) -> str:
        return name.strip().title()
