"""Entry point for WinEnhanceMouse."""
from __future__ import annotations

import logging
import sys

from .engine import Engine


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
    try:
        engine = Engine()
        engine.start()
    except KeyboardInterrupt:
        print("\nWinEnhanceMouse stopped by user.")
    except Exception as exc:  # noqa: BLE001
        logging.exception("WinEnhanceMouse crashed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
