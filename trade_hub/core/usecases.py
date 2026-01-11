"""Business logic."""

from datetime import datetime

from trade_hub.core.currencies import get_currency
from trade_hub.core.exceptions import (
    AuthenticationError,
    CurrencyNotFoundError,
    UserNotFoundError,
    ValidationError,
)
from trade_hub.core.models import Portfolio, User
from trade_hub.decorators import log_action
from trade_hub.infra.database import db
from trade_hub.infra.settings import settings


class UserSession:
    """Manages current user session."""

    _current_user: User | None = None

    @classmethod
    def login(cls, user: User):
        """Set current logged in user."""
        cls._current_user = user

    @classmethod
    def logout(cls):
        """Clear current session."""
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> User | None:
        """Get currently logged in user."""
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        """Check if user is logged in."""
        return cls._current_user is not None


@log_action("REGISTER")
def register_user(username: str, password: str) -> User:
    """Register new user."""
    if not username or not username.strip():
        raise ValidationError("Username cannot be empty")
    if len(password) < 4:
        raise ValidationError("Password must be at least 4 characters long")

    username = username.strip()
    users_data = db.load_users()

    for user_data in users_data:
        if user_data["username"].lower() == username.lower():
            raise ValidationError(f"Username '{username}' is already taken")

    new_id = max((u["user_id"] for u in users_data), default=0) + 1

    user = User(
        user_id=new_id,
        username=username,
        password=password,
        registration_date=datetime.now(),
    )

    users_data.append(user.to_dict())
    db.save_users(users_data)

    portfolios_data = db.load_portfolios()
    portfolio = Portfolio(user_id=new_id)
    portfolios_data.append(portfolio.to_dict())
    db.save_portfolios(portfolios_data)

    return user


@log_action("LOGIN")
def login_user(username: str, password: str) -> User:
    """Authenticate and login user."""
    users_data = db.load_users()

    for user_data in users_data:
        if user_data["username"].lower() == username.lower():
            user = User.from_dict(user_data)
            if user.verify_password(password):
                UserSession.login(user)
                return user
            else:
                raise AuthenticationError("Invalid password")

    raise UserNotFoundError(username)


def get_portfolio(user_id: int) -> Portfolio:
    """Get user portfolio."""
    portfolios_data = db.load_portfolios()

    for portfolio_data in portfolios_data:
        if portfolio_data["user_id"] == user_id:
            return Portfolio.from_dict(portfolio_data)

    return Portfolio(user_id=user_id)


def save_portfolio(portfolio: Portfolio):
    """Save portfolio to storage."""
    portfolios_data = db.load_portfolios()

    for i, p in enumerate(portfolios_data):
        if p["user_id"] == portfolio.user_id:
            portfolios_data[i] = portfolio.to_dict()
            break
    else:
        portfolios_data.append(portfolio.to_dict())

    db.save_portfolios(portfolios_data)


def get_rates() -> dict:
    """Get exchange rates from cache."""
    return db.load_rates()


def get_rate(from_currency: str, to_currency: str) -> dict | None:
    """Get specific exchange rate."""
    from_code = from_currency.strip().upper()
    to_code = to_currency.strip().upper()

    # Validate currency codes exist in registry
    get_currency(from_code)
    get_currency(to_code)

    if from_code == to_code:
        return {"rate": 1.0, "updated_at": datetime.now().isoformat()}

    rates = get_rates()
    rate_key = f"{from_code}_{to_code}"

    # Check TTL
    ttl = settings.rates_ttl

    if rate_key in rates:
        rate_data = rates[rate_key]
        updated_at = rate_data.get("updated_at")
        if updated_at:
            try:
                updated_time = datetime.fromisoformat(updated_at)
                age = (datetime.now() - updated_time).total_seconds()
                if age > ttl:
                    pass  # Rate is stale, but we return it with warning
            except (ValueError, TypeError):
                pass
        return rate_data

    reverse_key = f"{to_code}_{from_code}"
    if reverse_key in rates and rates[reverse_key].get("rate"):
        reverse_rate = rates[reverse_key]["rate"]
        return {
            "rate": 1.0 / reverse_rate,
            "updated_at": rates[reverse_key].get("updated_at"),
        }

    raise CurrencyNotFoundError(f"{from_code}->{to_code}")


@log_action("BUY", verbose=True)
def buy_currency(currency_code: str, amount: float) -> dict:
    """Buy specified currency."""
    if not UserSession.is_logged_in():
        raise PermissionError("Please login first")

    code = currency_code.strip().upper()
    get_currency(code)

    # Validate amount
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValidationError("Amount must be a positive number")

    user = UserSession.get_current_user()
    portfolio = get_portfolio(user.user_id)

    wallet = portfolio.get_wallet(code)
    old_balance = wallet.balance if wallet else 0.0

    wallet = portfolio.add_currency(code)
    wallet.deposit(amount)

    save_portfolio(portfolio)

    rate_info = None
    try:
        rate_info = get_rate(code, "USD")
    except CurrencyNotFoundError:
        pass

    rate = rate_info["rate"] if rate_info else None
    estimated_value = amount * rate if rate else None

    return {
        "currency": code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": rate,
        "estimated_value_usd": estimated_value,
    }


@log_action("SELL", verbose=True)
def sell_currency(currency_code: str, amount: float) -> dict:
    """Sell specified currency."""
    if not UserSession.is_logged_in():
        raise PermissionError("Please login first")

    code = currency_code.strip().upper()
    get_currency(code)

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValidationError("Amount must be a positive number")

    user = UserSession.get_current_user()
    portfolio = get_portfolio(user.user_id)

    wallet = portfolio.get_wallet(code)
    if not wallet:
        raise ValidationError(
            f"You don't have a '{code}' wallet. "
            "Add currency: it is created automatically on first purchase."
        )

    old_balance = wallet.balance

    # This will raise InsufficientFundsError if not enough balance
    wallet.withdraw(amount)

    save_portfolio(portfolio)

    rate_info = None
    try:
        rate_info = get_rate(code, "USD")
    except CurrencyNotFoundError:
        pass

    rate = rate_info["rate"] if rate_info else None
    estimated_value = amount * rate if rate else None

    return {
        "currency": code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "rate": rate,
        "estimated_value_usd": estimated_value,
    }
