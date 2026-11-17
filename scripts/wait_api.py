"""Wait for a ready API without generating answers."""

import sys
import time
import urllib.error
import urllib.request

for attempt in range(90):
    try:
        with urllib.request.urlopen(sys.argv[1].rstrip("/") + "/health", timeout=5) as response:
            if response.status == 200:
                print("API ready")
                break
    except (urllib.error.URLError, TimeoutError):
        pass
    time.sleep(2)
else:
    raise SystemExit("API did not become ready within the startup budget")
