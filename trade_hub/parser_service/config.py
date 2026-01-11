"""Parser config."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParserConfig:
    """Configuration for API clients and parser settings."""

    # API key loaded from environment variable
    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY", "")
    )

    # API endpoints
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Base currency for all conversions
    BASE_CURRENCY: str = "USD"

    # Fiat currencies to track
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB", "JPY", "CNY")

    # Crypto currencies to track
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "LTC", "XRP", "DOGE")

    # Mapping from ticker to CoinGecko ID
    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "XRP": "ripple",
        "DOGE": "dogecoin",
    })

    # File paths
    DATA_DIR: Path = field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "data"
    )

    @property
    def rates_file_path(self) -> Path:
        """Path to rates.json cache file."""
        return self.DATA_DIR / "rates.json"

    @property
    def history_file_path(self) -> Path:
        """Path to exchange_rates.json history file."""
        return self.DATA_DIR / "exchange_rates.json"

    # Network parameters
    REQUEST_TIMEOUT: int = 10

    def get_coingecko_url(self) -> str:
        """Build CoinGecko API URL with configured currencies."""
        ids = ",".join(self.CRYPTO_ID_MAP.values())
        return f"{self.COINGECKO_URL}?ids={ids}&vs_currencies={self.BASE_CURRENCY.lower()}"

    def get_exchangerate_url(self) -> str:
        """Build ExchangeRate-API URL with API key."""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError("EXCHANGERATE_API_KEY environment variable not set")
        key = self.EXCHANGERATE_API_KEY
        return f"{self.EXCHANGERATE_API_URL}/{key}/latest/{self.BASE_CURRENCY}"


parser_config = ParserConfig()

