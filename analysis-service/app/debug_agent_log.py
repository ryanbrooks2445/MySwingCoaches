"""Session debug logging (agent instrumentation)."""

from __future__ import annotations

import json
import time

_DEBUG_LOG_PATH = "/Users/ryanbrooks/Desktop/MySwingCoaches/.cursor/debug-c91b3a.log"
_SESSION_ID = "c91b3a"


def agent_log(
    *,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict,
    run_id: str = "pre-fix",
) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": _SESSION_ID,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except OSError:
        pass
    # endregion
