"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """Store request provenance and return its correlation ID."""
        correlation_id = request_id or f"REQ-{uuid.uuid4().hex[:12].upper()}"
        self._open[correlation_id] = {
            "request_id": correlation_id,
            "user_id": user_id,
            "input": text,
            "input_timestamp": utc_now_iso(),
            "started_monotonic": time.monotonic(),
        }
        return correlation_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
        action: str | None = None,
        reviewer_id: str | None = None,
        reviewer_decision: str | None = None,
    ):
        """Finish an audit record using the same request ID as the input."""
        correlation_id = request_id
        if correlation_id is None:
            correlation_id = next(
                (
                    key
                    for key, pending in reversed(list(self._open.items()))
                    if pending["user_id"] == user_id
                ),
                None,
            )
        if correlation_id is None:
            correlation_id = self.record_input(user_id=user_id, text="")

        pending = self._open.pop(correlation_id, None) or {
            "request_id": correlation_id,
            "user_id": user_id,
            "input": "",
            "input_timestamp": utc_now_iso(),
            "started_monotonic": time.monotonic(),
        }
        started = pending.pop("started_monotonic")
        record = {
            **pending,
            "output": text,
            "output_timestamp": utc_now_iso(),
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
            "blocked": blocked,
            "layer": layer,
            "decision": "blocked" if blocked else "allowed",
            "action": action,
            "reviewer_id": reviewer_id,
            "reviewer_decision": reviewer_decision,
        }
        self.logs.append(record)
        return record

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.logs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
