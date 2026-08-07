"""
Assignment 11 — Rate Limiter starter (TODO).

Sliding-window, per-user rate limiting. Blocks abuse that other
guardrail layers do not address (flooding / cost attacks).
"""
from __future__ import annotations

from collections import defaultdict, deque
import time

from google.adk.plugins import base_plugin
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class RateLimitPlugin(base_plugin.BasePlugin):
    """Block users who exceed max_requests within window_seconds."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(name="rate_limiter")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows: dict[str, deque] = defaultdict(deque)
        self.blocked_count = 0
        self.total_count = 0
        self._blocked_responses: dict[str, types.Content] = {}

    def _block_response(self, message: str) -> types.Content:
        return types.Content(
            role="model",
            parts=[types.Part.from_text(text=message)],
        )

    async def on_user_message_callback(self, *, invocation_context, user_message):
        """Return Content to block, or None to allow."""
        self.total_count += 1
        user_id = getattr(invocation_context, "user_id", None) or "anonymous"
        now = time.time()
        window = self.user_windows[user_id]

        cutoff = now - self.window_seconds
        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= self.max_requests:
            wait = max(0.0, self.window_seconds - (now - window[0]))
            self.blocked_count += 1
            response = self._block_response(
                f"Rate limit exceeded. Try again in {wait:.0f}s."
            )
            invocation_id = getattr(invocation_context, "invocation_id", None)
            if invocation_id:
                self._blocked_responses[invocation_id] = response
            return response

        window.append(now)
        return None

    async def before_model_callback(
        self,
        *,
        callback_context,
        llm_request,
    ) -> LlmResponse | None:
        """Prevent a rate-limited request from reaching the model in ADK 2.x."""
        invocation_id = getattr(callback_context, "invocation_id", None)
        response = self._blocked_responses.pop(invocation_id, None)
        if response is None:
            return None
        return LlmResponse(content=response)
