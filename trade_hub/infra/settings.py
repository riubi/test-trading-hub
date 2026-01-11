"""Application settings."""

import json
from pathlib import Path
from typing import Any


class SettingsLoader:
    """
    Singleton for loading and caching application settings.
    """

    _instance = None
    _initialized = False

    DEFAULTS = {
        "data_dir": "data",
        "users_file": "users.json",
        "portfolios_file": "portfolios.json",
        "rates_file": "rates.json",
        "rates_ttl_seconds": 300,  # 5 minutes
        "default_base_currency": "USD",
        "log_dir": "logs",
        "log_file": "actions.log",
        "log_format": "string",  # "string" or "json"
        "log_level": "INFO",
        "log_max_size_mb": 10,
        "log_backup_count": 5,
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SettingsLoader._initialized:
            return
        self._config = dict(self.DEFAULTS)
        self._load_config()
        SettingsLoader._initialized = True

    def _load_config(self):
        """Load configuration from config.json if exists."""
        config_path = Path(__file__).parent.parent.parent / "config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    user_config = json.load(f)
                    self._config.update(user_config)
            except (json.JSONDecodeError, OSError):
                pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default if default is not None else self.DEFAULTS.get(key))

    def reload(self):
        """Reload configuration from file."""
        self._config = dict(self.DEFAULTS)
        self._load_config()

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return Path(__file__).parent.parent.parent / self.get("data_dir")

    @property
    def rates_ttl(self) -> int:
        """Get rates TTL in seconds."""
        return self.get("rates_ttl_seconds")

    @property
    def default_base_currency(self) -> str:
        """Get default base currency."""
        return self.get("default_base_currency")

    @property
    def log_dir(self) -> Path:
        """Get log directory path."""
        return Path(__file__).parent.parent.parent / self.get("log_dir")


settings = SettingsLoader()

