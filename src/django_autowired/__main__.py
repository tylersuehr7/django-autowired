"""Entry point for ``python -m django_autowired``."""

import sys

from django_autowired.cli import main

if __name__ == "__main__":
    sys.exit(main())
