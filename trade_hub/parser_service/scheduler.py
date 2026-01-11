"""Update scheduler."""

import logging
import threading

from trade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger("trade_hub.parser")


class RatesScheduler:
    """Schedules periodic rate updates."""

    def __init__(self, interval_seconds: int = 300, updater: RatesUpdater = None):
        self.interval = interval_seconds
        self.updater = updater or RatesUpdater()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Start the scheduler in background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started with {self.interval}s interval")

    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                self.updater.run_update()
            except Exception as e:
                logger.error(f"Scheduled update failed: {e}")

            # Wait for interval or until stopped
            self._stop_event.wait(timeout=self.interval)

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._thread is not None and self._thread.is_alive()

