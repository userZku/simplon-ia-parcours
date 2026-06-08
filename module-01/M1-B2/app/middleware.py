"""Logging middleware with request_id and latency tracking.

Adds X-Request-ID to every response and logs structured JSON to file.
"""
from __future__ import annotations

import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log each request: method, path, status, latency, request_id."""

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        if path == "/":
            return "/"
        return path.rstrip("/")

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        endpoint = self._normalize_endpoint(request.url.path)

        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logger.bind(request__id=request_id, endpoint=endpoint).exception(
                "Unhandled exception in request"
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
            status_code = 500

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        log_level = (
            "INFO" if status_code < 400
            else "WARNING" if status_code < 500
            else "ERROR"
        )

        logger.bind(
            request__id=request_id,
            method=request.method,
            path=request.url.path,
            endpoint=endpoint,
            status=status_code,
            latency__ms=latency_ms,
        ).log(
            log_level,
            "request_completed",
        )

        response.headers["X-Request-ID"] = request_id
        return response
