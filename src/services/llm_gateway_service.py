"""LLM Gateway Service – unified LLM call entry point with routing, rate-limiting, retry, and cost tracking."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from repositories.llm_call_log_repository import LLMCallLogRepository


# ── Provider Protocols ──────────────────────

@runtime_checkable
class LLMProvider(Protocol):
    def chat(self, messages: list[dict], **kwargs: Any) -> dict: ...
    def models(self) -> list[str]: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


# ── Gateway Error ───────────────────────────

class GatewayError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"LLM_GATEWAY_ERROR: {message}")


# ── Gateway Service ─────────────────────────

class LLMGatewayService:
    def __init__(self, *, call_log_repo: LLMCallLogRepository) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._embedding_providers: dict[str, EmbeddingProvider] = {}
        self._routes: dict[str, tuple[str, str]] = {}  # task_type -> (provider_name, model)
        self._rate_limits: dict[str, int] = {}  # provider_name -> rpm
        self._rate_windows: dict[str, list[float]] = {}  # provider_name -> timestamps
        self._rate_window_seconds: dict[str, float] = {}  # provider_name -> window size
        self._max_retries: int = 1
        self._call_log_repo = call_log_repo

    # ── Provider management ────────────────

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    def register_embedding_provider(self, name: str, provider: EmbeddingProvider) -> None:
        self._embedding_providers[name] = provider

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    # ── Route configuration ────────────────

    def set_route(self, task_type: str, *, provider_name: str, model: str) -> None:
        self._routes[task_type] = (provider_name, model)

    def set_rate_limit(self, provider_name: str, *, rpm: int, window_seconds: float = 60.0) -> None:
        self._rate_limits[provider_name] = rpm
        self._rate_windows.setdefault(provider_name, [])
        self._rate_window_seconds[provider_name] = window_seconds

    def set_retry(self, *, max_retries: int) -> None:
        self._max_retries = max_retries

    # ── Core operations ────────────────────

    def chat_completion(self, *, task_type: str, messages: list[dict], **kwargs: Any) -> dict:
        route = self._routes.get(task_type)
        if route is None:
            raise GatewayError(f"no route configured for task_type={task_type}")

        provider_name, model = route
        provider = self._providers.get(provider_name)
        if provider is None:
            raise GatewayError(f"provider '{provider_name}' not registered")

        self._wait_rate_limit(provider_name)

        start_ms = time.monotonic_ns() // 1_000_000
        last_error: Exception | None = None
        result: dict | None = None

        for attempt in range(self._max_retries):
            try:
                result = provider.chat(messages, model=model, **kwargs)
                last_error = None
                break
            except Exception as e:
                last_error = e

        latency_ms = (time.monotonic_ns() // 1_000_000) - start_ms

        if last_error is not None:
            self._call_log_repo.write_log(
                call_type=task_type,
                provider=provider_name,
                model=model,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                cost_estimate=0.0,
                status="failed",
            )
            raise GatewayError(str(last_error))

        usage = result.get("usage", {}) if result else {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        self._call_log_repo.write_log(
            call_type=task_type,
            provider=provider_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_estimate=0.0,
            status="success",
        )

        return result  # type: ignore[return-value]

    def embed(self, *, texts: list[str]) -> list[list[float]]:
        route = self._routes.get("embedding")
        if route is None:
            raise GatewayError("no route configured for embedding")

        provider_name, _model = route
        emb_provider = self._embedding_providers.get(provider_name)
        if emb_provider is None:
            raise GatewayError(f"embedding provider '{provider_name}' not registered")

        return emb_provider.embed(texts)

    # ── Usage report ───────────────────────

    def get_usage_report(self, *, start_time: datetime, end_time: datetime) -> list[dict]:
        return self._call_log_repo.aggregate_usage(start_time=start_time, end_time=end_time)

    # ── API key helper ─────────────────────

    @staticmethod
    def get_api_key(env_var: str) -> str:
        value = os.environ.get(env_var)
        if not value:
            raise GatewayError(f"environment variable '{env_var}' not set")
        return value

    # ── Rate limiter ───────────────────────

    def _wait_rate_limit(self, provider_name: str) -> None:
        rpm = self._rate_limits.get(provider_name)
        if rpm is None:
            return

        window_sec = self._rate_window_seconds.get(provider_name, 60.0)
        window = self._rate_windows.setdefault(provider_name, [])
        now = time.monotonic()
        cutoff = now - window_sec
        self._rate_windows[provider_name] = [t for t in window if t > cutoff]
        window = self._rate_windows[provider_name]

        if len(window) >= rpm:
            sleep_time = window_sec - (now - window[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._rate_windows[provider_name] = [t for t in window if t > time.monotonic() - window_sec]

        self._rate_windows[provider_name].append(time.monotonic())
