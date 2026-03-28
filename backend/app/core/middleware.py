"""
Rate Limiter Middleware + Security Headers.
"""
import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from backend.app.core.config import settings
from loguru import logger


# ═══════════════════════════════════════════════════════════════
#  IN-MEMORY RATE LIMITER
# ═══════════════════════════════════════════════════════════════

class RateLimitStore:
    """IP başına istek sayacı (bellekte, sunucu yeniden başlatılınca sıfırlanır)."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, ip: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        # Eski istekleri temizle
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]
        if len(self._requests[ip]) >= max_requests:
            return True
        self._requests[ip].append(now)
        return False


_rate_store = RateLimitStore()


# ═══════════════════════════════════════════════════════════════
#  RATE LIMITER MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # WebSocket bağlantıları hariç tut
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        if _rate_store.is_rate_limited(client_ip, settings.RATE_LIMIT_PER_MINUTE):
            logger.warning(f"Rate limit aşıldı: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Çok fazla istek. Lütfen bir dakika bekleyin."},
            )

        response = await call_next(request)
        return response


# ═══════════════════════════════════════════════════════════════
#  SECURITY HEADERS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response


# ═══════════════════════════════════════════════════════════════
#  REQUEST LOGGER MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)
        client_ip = request.client.host if request.client else "?"
        logger.info(f"[{client_ip}] {request.method} {request.url.path} → {response.status_code} ({duration}ms)")
        return response
