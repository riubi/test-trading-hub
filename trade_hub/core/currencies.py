"""Currency types."""

from abc import ABC, abstractmethod


class Currency(ABC):
    """Abstract base class for all currencies."""

    def __init__(self, code: str, name: str):
        if not code or not code.strip():
            raise ValueError("Currency code cannot be empty")
        if not name or not name.strip():
            raise ValueError("Currency name cannot be empty")

        code = code.strip().upper()
        if len(code) < 2 or len(code) > 5:
            raise ValueError("Currency code must be 2-5 characters")
        if " " in code:
            raise ValueError("Currency code cannot contain spaces")

        self.code = code
        self.name = name.strip()

    @abstractmethod
    def get_display_info(self) -> str:
        """Get formatted display string for UI/logs."""
        pass


class FiatCurrency(Currency):
    """Fiat currency issued by a country or zone."""

    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Get formatted display string."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Cryptocurrency with algorithm and market cap."""

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """Get formatted display string."""
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap else "N/A"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# Currency registry
CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "GBP": FiatCurrency("GBP", "British Pound", "United Kingdom"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "JPY": FiatCurrency("JPY", "Japanese Yen", "Japan"),
    "CNY": FiatCurrency("CNY", "Chinese Yuan", "China"),
    # Cryptocurrencies
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.5e11),
    "LTC": CryptoCurrency("LTC", "Litecoin", "Scrypt", 6.5e9),
    "XRP": CryptoCurrency("XRP", "Ripple", "RPCA", 2.8e10),
    "DOGE": CryptoCurrency("DOGE", "Dogecoin", "Scrypt", 1.2e10),
}


def get_currency(code: str) -> Currency:
    """Get currency by code from registry."""
    from trade_hub.core.exceptions import CurrencyNotFoundError

    if not code:
        raise CurrencyNotFoundError(code)

    code = code.strip().upper()
    if code not in CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)

    return CURRENCY_REGISTRY[code]


def get_supported_currencies() -> list[str]:
    """Get list of supported currency codes."""
    return list(CURRENCY_REGISTRY.keys())


def is_fiat(code: str) -> bool:
    """Check if currency is fiat."""
    try:
        currency = get_currency(code)
        return isinstance(currency, FiatCurrency)
    except Exception:
        return False


def is_crypto(code: str) -> bool:
    """Check if currency is cryptocurrency."""
    try:
        currency = get_currency(code)
        return isinstance(currency, CryptoCurrency)
    except Exception:
        return False

