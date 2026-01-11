"""Rates updater."""

import logging
from datetime import datetime, timezone

from trade_hub.core.exceptions import ApiRequestError
from trade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from trade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger("trade_hub.parser")


class RatesUpdater:
    """Coordinates rate updates from multiple sources."""

    def __init__(
        self,
        clients: list[BaseApiClient] = None,
        storage: RatesStorage = None,
    ):
        self.clients = clients or [CoinGeckoClient(), ExchangeRateApiClient()]
        self.storage = storage or RatesStorage()

    def run_update(self, source: str = None) -> dict:
        """
        Run rate update from all or specified sources.

        Args:
            source: Optional source filter ("coingecko" or "exchangerate")

        Returns:
            dict with update results: {
                "success": bool,
                "total_rates": int,
                "sources": {source_name: {"rates": int, "error": str|None}},
                "last_refresh": str
            }
        """
        logger.info("Starting rates update...")
        results = {
            "success": True,
            "total_rates": 0,
            "sources": {},
            "errors": [],
            "last_refresh": None,
        }

        all_rates = {}
        clients_to_use = self._filter_clients(source)

        for client in clients_to_use:
            source_name = client.source_name
            logger.info(f"Fetching from {source_name}...")

            try:
                rates = client.fetch_rates()
                all_rates.update(rates)
                results["sources"][source_name] = {
                    "rates": len(rates),
                    "error": None,
                }
                logger.info(f"{source_name}: OK ({len(rates)} rates)")

            except ApiRequestError as e:
                error_msg = str(e)
                results["sources"][source_name] = {
                    "rates": 0,
                    "error": error_msg,
                }
                results["errors"].append(f"{source_name}: {error_msg}")
                logger.error(f"{source_name}: FAILED - {error_msg}")

        if all_rates:
            self.storage.save_rates(all_rates)
            self.storage.save_to_history(all_rates)
            results["total_rates"] = len(all_rates)
            results["last_refresh"] = datetime.now(timezone.utc).isoformat()
        else:
            results["success"] = False

        if results["errors"]:
            results["success"] = len(all_rates) > 0  # Partial success

        logger.info(
            f"Update completed: {results['total_rates']} rates, "
            f"{len(results['errors'])} errors"
        )
        return results

    def _filter_clients(self, source: str = None) -> list[BaseApiClient]:
        """Filter clients by source name."""
        if not source:
            return self.clients

        source = source.lower()
        filtered = []
        for client in self.clients:
            name = client.source_name.lower()
            if source in name or name in source:
                filtered.append(client)

        return filtered if filtered else self.clients

    def update_crypto_only(self) -> dict:
        """Update only cryptocurrency rates."""
        return self.run_update(source="coingecko")

    def update_fiat_only(self) -> dict:
        """Update only fiat currency rates."""
        return self.run_update(source="exchangerate")

