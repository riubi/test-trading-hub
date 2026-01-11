# Trade Hub

Console application for currency trading simulation.

## Installation

```bash
make install
```

## Usage

```bash
make project
# or
poetry run project
```

## Commands

| Command | Description |
|---------|-------------|
| `register --username <name> --password <pass>` | Register new user |
| `login --username <name> --password <pass>` | Login |
| `show-portfolio [--base <currency>]` | Show portfolio |
| `buy --currency <code> --amount <num>` | Buy currency |
| `sell --currency <code> --amount <num>` | Sell currency |
| `get-rate --from <code> --to <code>` | Get exchange rate |
| `update-rates [--source <name>]` | Update rates from API |
| `show-rates [--currency <code>] [--top <n>]` | Show cached rates |
| `currencies` | List supported currencies |

## Test Users

| Username | Password |
|----------|----------|
| testuser | test123 |
| admin | short |

## Notes

- `buy` adds currency to portfolio (simulation mode, no USD deduction)
- `sell` checks wallet balance and shows "Insufficient funds" error if needed

## Examples

```
> login --username testuser --password test123
> buy --currency BTC --amount 0.05
> show-portfolio
> sell --currency BTC --amount 0.01
> get-rate --from BTC --to USD
```

## Parser Service

To update rates from external APIs:

```bash
export EXCHANGERATE_API_KEY="your_key_here"
```

Get API key at: https://www.exchangerate-api.com/

```
> update-rates                       # Update all rates
> update-rates --source coingecko    # Crypto only
> update-rates --source exchangerate # Fiat only
```

Rates are cached in `data/rates.json` with TTL of 5 minutes.

## Project Structure

```
trade_hub/
├── core/           # Business logic (models, usecases)
├── cli/            # Command-line interface
├── infra/          # Settings, database
└── parser_service/ # API clients, rate updates
data/
├── users.json      # User accounts
├── portfolios.json # User portfolios
└── rates.json      # Exchange rates cache
```

## Demo

[![asciicast](https://asciinema.org/a/WxDNyD5CsezBqkSO.svg)](https://asciinema.org/a/WxDNyD5CsezBqkSO)
