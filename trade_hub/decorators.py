"""Decorators."""

import functools
import logging

logger = logging.getLogger("trade_hub")


def log_action(action_name: str = None, verbose: bool = False):
    """
    Decorator for logging domain operations.

    Logs operation details at INFO level including:
    - timestamp, action name, parameters, result status

    Does not suppress exceptions - logs them and re-raises.

    Args:
        action_name: Name of action for logs (e.g., "BUY", "SELL")
        verbose: If True, include additional context in logs
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = action_name or func.__name__.upper()

            # Extract relevant info from kwargs
            username = kwargs.get("username", "N/A")
            user_id = kwargs.get("user_id", "N/A")
            currency = kwargs.get("currency_code", kwargs.get("currency", "N/A"))
            amount = kwargs.get("amount", "N/A")

            # Build log message parts
            log_parts = [
                f"{name}",
                f"user='{username if username != 'N/A' else user_id}'",
            ]

            if currency != "N/A":
                log_parts.append(f"currency='{currency}'")
            if amount != "N/A":
                log_parts.append(f"amount={amount}")

            try:
                result = func(*args, **kwargs)

                # Add result info for verbose mode
                if verbose and isinstance(result, dict):
                    rate = result.get("rate")
                    if rate:
                        log_parts.append(f"rate={rate:.2f}")
                        log_parts.append("base='USD'")

                log_parts.append("result=OK")
                logger.info(" ".join(log_parts))

                return result

            except Exception as e:
                log_parts.append("result=ERROR")
                log_parts.append(f"error_type={type(e).__name__}")
                log_parts.append(f"error_message='{str(e)}'")
                logger.error(" ".join(log_parts))
                raise

        return wrapper

    return decorator


def require_login(func):
    """Decorator that requires user to be logged in."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from trade_hub.core.usecases import UserSession

        if not UserSession.is_logged_in():
            raise PermissionError("Please login first")
        return func(*args, **kwargs)

    return wrapper
