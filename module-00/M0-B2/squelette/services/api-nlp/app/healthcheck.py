"""Healthcheck applicatif avec retry court pour Docker Compose."""
from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request


HEALTH_URL = os.getenv("HEALTHCHECK_URL", "http://localhost:8000/health")
RETRIES = int(os.getenv("HEALTHCHECK_RETRIES", "5"))
DELAY_SECONDS = float(os.getenv("HEALTHCHECK_DELAY_SECONDS", "0.5"))
TIMEOUT_SECONDS = float(os.getenv("HEALTHCHECK_TIMEOUT_SECONDS", "2"))


def main() -> int:
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=TIMEOUT_SECONDS) as response:
                if 200 <= response.status < 300:
                    return 0
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass

        if attempt < RETRIES:
            time.sleep(DELAY_SECONDS)

    return 1


if __name__ == "__main__":
    sys.exit(main())
