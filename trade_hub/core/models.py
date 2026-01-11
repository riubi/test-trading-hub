"""Domain models."""

import hashlib
import secrets
from datetime import datetime

from trade_hub.core.exceptions import InsufficientFundsError, ValidationError


class User:
    """User account in the trading system."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str = None,
        hashed_password: str = None,
        salt: str = None,
        registration_date: datetime = None,
    ):
        self._user_id = user_id
        self._username = None
        self.username = username

        if hashed_password and salt:
            self._hashed_password = hashed_password
            self._salt = salt
        else:
            if password and len(password) < 4:
                raise ValidationError("Password must be at least 4 characters long")
            self._salt = secrets.token_hex(8)
            self._hashed_password = self._hash_password(password, self._salt)

        self._registration_date = registration_date or datetime.now()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Hash password with salt using SHA-256."""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @property
    def user_id(self) -> int:
        """Get user ID."""
        return self._user_id

    @property
    def username(self) -> str:
        """Get username."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Set username with validation."""
        if not value or not value.strip():
            raise ValidationError("Username cannot be empty")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        """Get hashed password."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Get password salt."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Get registration date."""
        return self._registration_date

    def verify_password(self, password: str) -> bool:
        """Verify if provided password matches stored hash."""
        return self._hash_password(password, self._salt) == self._hashed_password

    def change_password(self, new_password: str):
        """Change user password."""
        if len(new_password) < 4:
            raise ValidationError("Password must be at least 4 characters long")
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash_password(new_password, self._salt)

    def get_user_info(self) -> dict:
        """Get user information without password."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def to_dict(self) -> dict:
        """Convert user to dictionary for JSON storage."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User instance from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )


class Wallet:
    """Wallet for a single currency."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        """Get current balance."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Set balance with validation."""
        if not isinstance(value, (int, float)):
            raise TypeError("Balance must be a number")
        if value < 0:
            raise ValidationError("Balance cannot be negative")
        self._balance = float(value)

    def deposit(self, amount: float):
        """Add funds to wallet."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        self._balance += amount

    def withdraw(self, amount: float):
        """Remove funds from wallet."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a number")
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        if amount > self._balance:
            raise InsufficientFundsError(
                available=self._balance,
                required=amount,
                code=self.currency_code,
            )
        self._balance -= amount

    def get_balance_info(self) -> str:
        """Get formatted balance information."""
        return f"{self.currency_code}: {self._balance:.4f}"

    def to_dict(self) -> dict:
        """Convert wallet to dictionary."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Create Wallet instance from dictionary."""
        return cls(
            currency_code=data.get("currency_code", ""),
            balance=data.get("balance", 0.0),
        )


class Portfolio:
    """Collection of wallets for a single user."""

    def __init__(self, user_id: int, wallets: dict = None):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = {}

        if wallets:
            for code, wallet_data in wallets.items():
                if isinstance(wallet_data, Wallet):
                    self._wallets[code.upper()] = wallet_data
                elif isinstance(wallet_data, dict):
                    self._wallets[code.upper()] = Wallet(
                        currency_code=code,
                        balance=wallet_data.get("balance", 0.0),
                    )

    @property
    def user_id(self) -> int:
        """Get user ID (read-only)."""
        return self._user_id

    @property
    def wallets(self) -> dict:
        """Get copy of wallets dictionary."""
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        """Add new wallet for currency if not exists."""
        code = currency_code.upper()
        if code not in self._wallets:
            self._wallets[code] = Wallet(currency_code=code)
        return self._wallets[code]

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Get wallet by currency code."""
        return self._wallets.get(currency_code.upper())

    def get_total_value(self, rates: dict, base_currency: str = "USD") -> float:
        """Calculate total portfolio value in base currency."""
        total = 0.0
        base = base_currency.upper()

        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
            else:
                rate_key = f"{code}_{base}"
                if rate_key in rates and rates[rate_key].get("rate"):
                    total += wallet.balance * rates[rate_key]["rate"]

        return total

    def to_dict(self) -> dict:
        """Convert portfolio to dictionary."""
        return {
            "user_id": self._user_id,
            "wallets": {
                code: {"balance": wallet.balance} for code, wallet in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Create Portfolio instance from dictionary."""
        return cls(
            user_id=data["user_id"],
            wallets=data.get("wallets", {}),
        )
