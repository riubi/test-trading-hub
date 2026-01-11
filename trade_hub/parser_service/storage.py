"""Rates storage."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from trade_hub.parser_service.config import parser_config

logger = logging.getLogger("trade_hub.parser")


class RatesStorage:
    """Handles reading and writing of exchange rates files."""

    def __init__(self, rates_path: Path = None, history_path: Path = None):
        self.rates_path = rates_path or parser_config.rates_file_path
        self.history_path = history_path or parser_config.history_file_path
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        self.rates_path.parent.mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, path: Path, data: dict):
        """Write data atomically using temp file and rename."""
        temp_path = path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(path)
        except OSError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def load_rates(self) -> dict:
        """Load current rates from cache file."""
        if not self.rates_path.exists():
            return {"pairs": {}, "last_refresh": None}
        try:
            with open(self.rates_path, encoding="utf-8") as f:
                data = json.load(f)

                if "pairs" not in data:
                    return {"pairs": data, "last_refresh": data.get("last_refresh")}
                return data
        except (json.JSONDecodeError, OSError):
            return {"pairs": {}, "last_refresh": None}

    def save_rates(self, rates: dict):
        """
        Save rates to cache file.

        Args:
            rates: Dict with rate data in format:
                   {"BTC_USD": {"rate": 59337.21, "updated_at": "...", "source": "..."}, ...}
        """
        current = self.load_rates()
        pairs = current.get("pairs", {})

        for key, value in rates.items():
            existing = pairs.get(key, {})
            existing_time = existing.get("updated_at", "")
            new_time = value.get("updated_at", "")

            if new_time >= existing_time:
                pairs[key] = {
                    "rate": value["rate"],
                    "updated_at": value["updated_at"],
                    "source": value.get("source", "unknown"),
                }

        timestamp = datetime.now(timezone.utc).isoformat()

        legacy_data = {}
        for key, value in pairs.items():
            legacy_data[key] = {
                "rate": value["rate"],
                "updated_at": value["updated_at"],
            }
        legacy_data["source"] = "ParserService"
        legacy_data["last_refresh"] = timestamp

        self._atomic_write(self.rates_path, legacy_data)
        logger.info(f"Saved {len(pairs)} rates to {self.rates_path}")

    def load_history(self) -> list:
        """Load historical rates from history file."""
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def save_to_history(self, rates: dict):
        """
        Append rates to history file.

        Each rate entry gets a unique ID based on currency pair and timestamp.
        """
        history = self.load_history()
        existing_ids = {entry.get("id") for entry in history}

        new_entries = []
        for key, value in rates.items():
            parts = key.split("_")
            if len(parts) != 2:
                continue

            from_curr, to_curr = parts
            timestamp = value.get("updated_at", datetime.now(timezone.utc).isoformat())

            entry_id = f"{from_curr}_{to_curr}_{timestamp}"

            if entry_id not in existing_ids:
                entry = {
                    "id": entry_id,
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "rate": value["rate"],
                    "timestamp": timestamp,
                    "source": value.get("source", "unknown"),
                    "meta": value.get("meta", {}),
                }
                new_entries.append(entry)
                existing_ids.add(entry_id)

        if new_entries:
            history.extend(new_entries)
            self._atomic_write(self.history_path, history)
            logger.info(f"Added {len(new_entries)} entries to history")

    def get_rate(self, from_currency: str, to_currency: str):
        """Get specific rate from cache."""
        rates = self.load_rates()
        pairs = rates.get("pairs", rates)  # Handle both formats
        key = f"{from_currency.upper()}_{to_currency.upper()}"
        return pairs.get(key)

    def get_all_rates(self) -> dict:
        """Get all rates from cache."""
        data = self.load_rates()
        if "pairs" in data:
            return data["pairs"]
        result = {}
        for k, v in data.items():
            if isinstance(v, dict) and "rate" in v:
                result[k] = v
        return result

