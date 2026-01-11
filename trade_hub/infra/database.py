"""Database manager for JSON storage."""

import json
from pathlib import Path
from typing import Any

from trade_hub.infra.settings import settings


class DatabaseManager:
    """
    Singleton for managing JSON file storage.

    Uses __new__ pattern for singleton implementation.
    Provides atomic read/write operations for data files.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if DatabaseManager._initialized:
            return
        self._ensure_data_dir()
        DatabaseManager._initialized = True

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        settings.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, filename: str) -> Path:
        """Get full path to data file."""
        return settings.data_dir / filename

    def load(self, filename: str) -> list | dict:
        """Load data from JSON file."""
        filepath = self._get_filepath(filename)
        if not filepath.exists():
            return [] if "rates" not in filename else {}
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return [] if "rates" not in filename else {}

    def save(self, filename: str, data: Any):
        """
        Save data to JSON file with atomic write.
        Uses temporary file and rename for atomicity.
        """
        self._ensure_data_dir()
        filepath = self._get_filepath(filename)
        temp_filepath = filepath.with_suffix(".tmp")

        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_filepath.replace(filepath)
        except OSError as e:
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise e

    def load_users(self) -> list:
        """Load users data."""
        return self.load(settings.get("users_file"))

    def save_users(self, data: list):
        """Save users data."""
        self.save(settings.get("users_file"), data)

    def load_portfolios(self) -> list:
        """Load portfolios data."""
        return self.load(settings.get("portfolios_file"))

    def save_portfolios(self, data: list):
        """Save portfolios data."""
        self.save(settings.get("portfolios_file"), data)

    def load_rates(self) -> dict:
        """Load rates data."""
        return self.load(settings.get("rates_file"))

    def save_rates(self, data: dict):
        """Save rates data."""
        self.save(settings.get("rates_file"), data)


# Global instance for easy access
db = DatabaseManager()

