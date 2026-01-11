"""Utility functions."""

from trade_hub.core.exceptions import ValidationError


def validate_currency_code(code: str) -> str:
    """Validate and normalize currency code."""
    if not code or not code.strip():
        raise ValidationError("Currency code cannot be empty")

    code = code.strip().upper()

    if len(code) < 2 or len(code) > 5:
        raise ValidationError("Currency code must be 2-5 characters")

    if " " in code:
        raise ValidationError("Currency code cannot contain spaces")

    return code


def validate_amount(amount) -> float:
    """Validate amount is positive number."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValidationError("Amount must be a number")

    if value <= 0:
        raise ValidationError("Amount must be positive")

    return value


def validate_username(username: str) -> str:
    """Validate username."""
    if not username or not username.strip():
        raise ValidationError("Username cannot be empty")
    return username.strip()


def validate_password(password: str) -> str:
    """Validate password meets requirements."""
    if not password:
        raise ValidationError("Password cannot be empty")
    if len(password) < 4:
        raise ValidationError("Password must be at least 4 characters long")
    return password


def format_currency_amount(amount: float, code: str) -> str:
    """Format currency amount for display."""
    if code in ("BTC", "ETH", "LTC", "XRP", "DOGE"):
        return f"{amount:.8f} {code}"
    return f"{amount:.2f} {code}"
