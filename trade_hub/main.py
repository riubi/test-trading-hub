"""Entry point."""

from trade_hub.cli.interface import run_cli
from trade_hub.logging_config import setup_logging


def main():
    """Application entry point."""
    setup_logging()
    run_cli()


if __name__ == "__main__":
    main()
