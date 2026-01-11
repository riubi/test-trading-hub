"""API clients."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests

from trade_hub.core.exceptions import ApiRequestError
from trade_hub.parser_service.config import parser_config

logger = logging.getLogger("trade_hub.parser")


class BaseApiClient(ABC):
    """Abstract base class for API clients."""

    @abstractmethod
    def fetch_rates(self) -> dict:
        """
        Fetch exchange rates from API.

        Returns:
            dict: Rates in format {"BTC_USD": {"rate": 59337.21, ...}, ...}
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass


class CoinGeckoClient(BaseApiClient):
    """Client for CoinGecko cryptocurrency API."""

    @property
    def source_name(self) -> str:
        return "CoinGecko"

    def fetch_rates(self) -> dict:
        """Fetch cryptocurrency rates from CoinGecko."""
        url = parser_config.get_coingecko_url()
        base = parser_config.BASE_CURRENCY.lower()

        logger.info(f"Fetching rates from CoinGecko: {url}")
        start_time = time.time()

        try:
            response = requests.get(url, timeout=parser_config.REQUEST_TIMEOUT)
            request_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 429:
                raise ApiRequestError("Rate limit exceeded (429). Try again later.")
            if response.status_code != 200:
                raise ApiRequestError(
                    f"CoinGecko returned status {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            timestamp = datetime.now(timezone.utc).isoformat()

            rates = {}
            # Reverse map: coingecko_id -> ticker
            id_to_ticker = {v: k for k, v in parser_config.CRYPTO_ID_MAP.items()}

            for coin_id, values in data.items():
                if coin_id in id_to_ticker and base in values:
                    ticker = id_to_ticker[coin_id]
                    rate_key = f"{ticker}_{parser_config.BASE_CURRENCY}"
                    rates[rate_key] = {
                        "rate": values[base],
                        "updated_at": timestamp,
                        "source": self.source_name,
                        "meta": {
                            "raw_id": coin_id,
                            "request_ms": request_ms,
                            "status_code": response.status_code,
                        },
                    }

            logger.info(f"CoinGecko: fetched {len(rates)} rates in {request_ms}ms")
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("CoinGecko request timed out")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Failed to connect to CoinGecko")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ApiRequestError(f"Failed to parse CoinGecko response: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Client for ExchangeRate-API fiat currency service."""

    @property
    def source_name(self) -> str:
        return "ExchangeRate-API"

    def fetch_rates(self) -> dict:
        """Fetch fiat currency rates from ExchangeRate-API."""
        try:
            url = parser_config.get_exchangerate_url()
        except ValueError as e:
            raise ApiRequestError(str(e))

        logger.info("Fetching rates from ExchangeRate-API")
        start_time = time.time()

        try:
            response = requests.get(url, timeout=parser_config.REQUEST_TIMEOUT)
            request_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 401:
                raise ApiRequestError("Invalid API key for ExchangeRate-API")
            if response.status_code == 429:
                raise ApiRequestError("Rate limit exceeded (429). Try again later.")
            if response.status_code != 200:
                raise ApiRequestError(
                    f"ExchangeRate-API returned status {response.status_code}"
                )

            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(
                    f"ExchangeRate-API error: {data.get('error-type', 'unknown')}"
                )

            api_rates = data.get("rates", {})
            timestamp = datetime.now(timezone.utc).isoformat()

            rates = {}
            base = parser_config.BASE_CURRENCY

            for currency in parser_config.FIAT_CURRENCIES:
                if currency in api_rates:
                    # Convert from BASE/CURRENCY to CURRENCY/BASE
                    # API gives USD->EUR rate, we want EUR->USD
                    rate_key = f"{currency}_{base}"
                    rates[rate_key] = {
                        "rate": api_rates[currency],
                        "updated_at": timestamp,
                        "source": self.source_name,
                        "meta": {
                            "request_ms": request_ms,
                            "status_code": response.status_code,
                        },
                    }

            logger.info(f"ExchangeRate-API: fetched {len(rates)} rates in {request_ms}ms")
            return rates

        except requests.exceptions.Timeout:
            raise ApiRequestError("ExchangeRate-API request timed out")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Failed to connect to ExchangeRate-API")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ApiRequestError(f"Failed to parse ExchangeRate-API response: {str(e)}")

