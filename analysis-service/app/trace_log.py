from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("swing.trace")


def log_trace(
    event: str,
    *,
    trace_id: str | None = None,
    user_id: str | None = None,
    report_id: str | None = None,
    status: str | None = None,
    error: str | None = None,
    **extra: Any,
) -> None:
    payload: dict[str, Any] = {
        "event": event,
        "trace_id": trace_id,
        "user_id": user_id,
        "report_id": report_id,
        "status": status,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    logger.info(json.dumps(payload, default=str))
