"""Custom exceptions."""


class TradeHubError(Exception):
    """Base exception for Trade Hub."""

    pass


class InsufficientFundsError(TradeHubError):
    """Raised when wallet has insufficient funds for withdrawal."""

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = (
            f"Insufficient funds: available {available:.4f} {code}, "
            f"required {required:.4f} {code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(TradeHubError):
    """Raised when currency code is not found in registry."""

    def __init__(self, code: str):
        self.code = code
        message = f"Unknown currency '{code}'"
        super().__init__(message)


class ApiRequestError(TradeHubError):
    """Raised when external API request fails."""

    def __init__(self, reason: str):
        self.reason = reason
        message = f"Error accessing external API: {reason}"
        super().__init__(message)


class UserNotFoundError(TradeHubError):
    """Raised when user is not found."""

    def __init__(self, username: str):
        self.username = username
        message = f"User '{username}' not found"
        super().__init__(message)


class AuthenticationError(TradeHubError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid password"):
        super().__init__(message)


class ValidationError(TradeHubError):
    """Raised when validation fails."""

    pass

