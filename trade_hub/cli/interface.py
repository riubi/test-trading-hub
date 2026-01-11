"""CLI commands."""

import shlex

from prettytable import PrettyTable

from trade_hub.core import usecases
from trade_hub.core.currencies import get_supported_currencies
from trade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    UserNotFoundError,
    ValidationError,
)


def parse_args(args_str: str) -> dict:
    """Parse command arguments into dictionary."""
    tokens = shlex.split(args_str)
    result = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--"):
            key = token[2:]
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                result[key] = tokens[i + 1]
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            i += 1
    return result


def cmd_register(args: dict):
    """Handle register command."""
    username = args.get("username")
    password = args.get("password")

    if not username:
        print("Error: --username is required")
        return
    if not password:
        print("Error: --password is required")
        return

    try:
        user = usecases.register_user(username=username, password=password)
        print(f"User '{user.username}' registered (id={user.user_id}).")
        print(f"Login: login --username {user.username} --password ****")
    except ValidationError as e:
        print(f"Error: {e}")


def cmd_login(args: dict):
    """Handle login command."""
    username = args.get("username")
    password = args.get("password")

    if not username:
        print("Error: --username is required")
        return
    if not password:
        print("Error: --password is required")
        return

    try:
        user = usecases.login_user(username=username, password=password)
        print(f"Logged in as '{user.username}'")
    except UserNotFoundError as e:
        print(f"Error: {e}")
    except AuthenticationError as e:
        print(f"Error: {e}")


def cmd_show_portfolio(args: dict):
    """Handle show-portfolio command."""
    if not usecases.UserSession.is_logged_in():
        print("Error: Please login first")
        return

    user = usecases.UserSession.get_current_user()
    base = args.get("base", "USD").upper()

    try:
        portfolio = usecases.get_portfolio(user.user_id)
        rates = usecases.get_rates()

        wallets = portfolio.wallets
        if not wallets:
            print(f"Portfolio of user '{user.username}' is empty.")
            return

        print(f"Portfolio of user '{user.username}' (base: {base}):")

        table = PrettyTable()
        table.field_names = ["Currency", "Balance", f"Value in {base}"]
        table.align["Currency"] = "l"
        table.align["Balance"] = "r"
        table.align[f"Value in {base}"] = "r"

        total = 0.0

        for code, wallet in wallets.items():
            balance = wallet.balance
            if code == base:
                value = balance
            else:
                rate_key = f"{code}_{base}"
                if rate_key in rates and rates[rate_key].get("rate"):
                    value = balance * rates[rate_key]["rate"]
                else:
                    value = None

            if value is not None:
                total += value
                table.add_row([code, f"{balance:.4f}", f"{value:.2f} {base}"])
            else:
                table.add_row([code, f"{balance:.4f}", "N/A"])

        print(table)
        print("-" * 40)
        print(f"TOTAL: {total:,.2f} {base}")

    except CurrencyNotFoundError as e:
        print(f"Error: {e}")
        print(f"Supported currencies: {', '.join(get_supported_currencies())}")


def cmd_buy(args: dict):
    """Handle buy command."""
    currency = args.get("currency")
    amount = args.get("amount")

    if not currency:
        print("Error: --currency is required")
        return
    if not amount:
        print("Error: --amount is required")
        return

    try:
        amount = float(amount)
        result = usecases.buy_currency(currency_code=currency, amount=amount)

        rate_str = f"{result['rate']:.2f}" if result["rate"] else "N/A"
        print(f"Purchase completed: {result['amount']:.4f} {result['currency']} "
              f"at rate {rate_str} USD/{result['currency']}")
        print("Portfolio changes:")
        print(f"  - {result['currency']}: was {result['old_balance']:.4f} "
              f"-> now {result['new_balance']:.4f}")

        if result["estimated_value_usd"]:
            print(f"Estimated purchase value: {result['estimated_value_usd']:,.2f} USD")

    except PermissionError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"Error: {e}")
    except CurrencyNotFoundError as e:
        print(f"Error: {e}")
        print(f"Supported currencies: {', '.join(get_supported_currencies())}")
    except ValueError:
        print("Error: 'amount' must be a positive number")


def cmd_sell(args: dict):
    """Handle sell command."""
    currency = args.get("currency")
    amount = args.get("amount")

    if not currency:
        print("Error: --currency is required")
        return
    if not amount:
        print("Error: --amount is required")
        return

    try:
        amount = float(amount)
        result = usecases.sell_currency(currency_code=currency, amount=amount)

        rate_str = f"{result['rate']:.2f}" if result["rate"] else "N/A"
        print(f"Sale completed: {result['amount']:.4f} {result['currency']} "
              f"at rate {rate_str} USD/{result['currency']}")
        print("Portfolio changes:")
        print(f"  - {result['currency']}: was {result['old_balance']:.4f} "
              f"-> now {result['new_balance']:.4f}")

        if result["estimated_value_usd"]:
            print(f"Estimated revenue: {result['estimated_value_usd']:,.2f} USD")

    except PermissionError as e:
        print(f"Error: {e}")
    except InsufficientFundsError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"Error: {e}")
    except CurrencyNotFoundError as e:
        print(f"Error: {e}")
        print(f"Supported currencies: {', '.join(get_supported_currencies())}")
    except ValueError:
        print("Error: 'amount' must be a positive number")


def cmd_get_rate(args: dict):
    """Handle get-rate command."""
    from_curr = args.get("from")
    to_curr = args.get("to")

    if not from_curr:
        print("Error: --from is required")
        return
    if not to_curr:
        print("Error: --to is required")
        return

    try:
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        rate_info = usecases.get_rate(from_curr, to_curr)

        if rate_info:
            rate = rate_info["rate"]
            updated = rate_info.get("updated_at", "N/A")
            print(f"Rate {from_curr}->{to_curr}: {rate:.8f} (updated: {updated})")

            if rate != 0:
                reverse = 1.0 / rate
                print(f"Reverse rate {to_curr}->{from_curr}: {reverse:.2f}")
        else:
            print(f"Rate {from_curr}->{to_curr} unavailable. Try again later.")

    except CurrencyNotFoundError as e:
        print(f"Error: {e}")
        print(f"Supported currencies: {', '.join(get_supported_currencies())}")
    except ApiRequestError as e:
        print(f"Error: {e}")
        print("Please try again later or check your network connection.")


def cmd_update_rates(args: dict):
    """Handle update-rates command."""
    from trade_hub.parser_service.updater import RatesUpdater

    source = args.get("source")

    print("INFO: Starting rates update...")

    try:
        updater = RatesUpdater()
        results = updater.run_update(source=source)

        for source_name, data in results["sources"].items():
            if data["error"]:
                print(f"ERROR: Failed to fetch from {source_name}: {data['error']}")
            else:
                print(f"INFO: Fetching from {source_name}... OK ({data['rates']} rates)")

        if results["total_rates"] > 0:
            print(f"INFO: Writing {results['total_rates']} rates to data/rates.json...")

        if results["errors"]:
            print("Update completed with errors. Check logs/actions.log for details.")
        else:
            print(f"Update successful. Total rates updated: {results['total_rates']}. "
                  f"Last refresh: {results['last_refresh']}")

    except ApiRequestError as e:
        print(f"ERROR: {e}")
        print("Please try again later or check your network connection.")
    except Exception as e:
        print(f"ERROR: Update failed: {e}")


def cmd_show_rates(args: dict):
    """Handle show-rates command."""
    from trade_hub.parser_service.storage import RatesStorage

    currency = args.get("currency")
    top = args.get("top")
    base = args.get("base", "USD").upper()

    storage = RatesStorage()
    rates = storage.get_all_rates()

    if not rates:
        print("Local rate cache is empty. Run 'update-rates' to load data.")
        return

    full_data = storage.load_rates()
    last_refresh = full_data.get("last_refresh", "N/A")

    print(f"Rates from cache (updated at {last_refresh}):")

    # Filter by currency if specified
    if currency:
        currency = currency.upper()
        filtered = {k: v for k, v in rates.items() if currency in k and isinstance(v, dict)}
        if not filtered:
            print(f"Rate for '{currency}' not found in cache.")
            return
        rates = filtered

    if base != "USD":
        filtered = {}
        for k, v in rates.items():
            if k.endswith(f"_{base}") and isinstance(v, dict):
                filtered[k] = v
        rates = filtered

    # Sort and limit for --top (filter out non-dict entries)
    items = [(k, v) for k, v in rates.items() if isinstance(v, dict) and "rate" in v]
    items.sort(key=lambda x: x[1].get("rate", 0), reverse=True)

    if top:
        try:
            top = int(top)
            items = items[:top]
        except ValueError:
            pass

    # Display rates
    table = PrettyTable()
    table.field_names = ["Pair", "Rate", "Source", "Updated"]
    table.align["Pair"] = "l"
    table.align["Rate"] = "r"
    table.align["Source"] = "l"
    table.align["Updated"] = "l"

    for key, data in items:
        rate = data.get("rate", 0)
        source = data.get("source", "N/A")
        updated = data.get("updated_at", "N/A")
        if updated and len(updated) > 19:
            updated = updated[:19]  # Truncate timezone
        table.add_row([key, f"{rate:.8f}", source, updated])

    print(table)


def cmd_help(_args: dict):
    """Show available commands."""
    print("Available commands:")
    print("  register --username <name> --password <pass>  - Register new user")
    print("  login --username <name> --password <pass>     - Login")
    print("  show-portfolio [--base <currency>]            - Show portfolio")
    print("  buy --currency <code> --amount <num>          - Buy currency")
    print("  sell --currency <code> --amount <num>         - Sell currency")
    print("  get-rate --from <code> --to <code>            - Get exchange rate")
    print("  update-rates [--source <name>]                - Update rates from APIs")
    print("  show-rates [--currency <code>] [--top <n>]    - Show cached rates")
    print("  currencies                                    - List supported currencies")
    print("  help                                          - Show this help")
    print("  exit                                          - Exit application")


def cmd_currencies(_args: dict):
    """Show list of supported currencies."""
    from trade_hub.core.currencies import CURRENCY_REGISTRY

    print("Supported currencies:")
    print()

    fiats = []
    cryptos = []

    for code, currency in CURRENCY_REGISTRY.items():
        info = currency.get_display_info()
        if "[FIAT]" in info:
            fiats.append(info)
        else:
            cryptos.append(info)

    print("Fiat currencies:")
    for info in fiats:
        print(f"  {info}")

    print()
    print("Cryptocurrencies:")
    for info in cryptos:
        print(f"  {info}")


COMMANDS = {
    "register": cmd_register,
    "login": cmd_login,
    "show-portfolio": cmd_show_portfolio,
    "buy": cmd_buy,
    "sell": cmd_sell,
    "get-rate": cmd_get_rate,
    "update-rates": cmd_update_rates,
    "show-rates": cmd_show_rates,
    "currencies": cmd_currencies,
    "help": cmd_help,
}


def run_cli():
    """Run interactive CLI."""
    print("Trade Hub - Currency Wallet Application")
    print("Type 'help' for available commands, 'exit' to quit.\n")

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue

            if line.lower() == "exit":
                print("Goodbye!")
                break

            parts = line.split(maxsplit=1)
            command = parts[0].lower()
            args_str = parts[1] if len(parts) > 1 else ""

            if command in COMMANDS:
                args = parse_args(args_str)
                COMMANDS[command](args)
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
