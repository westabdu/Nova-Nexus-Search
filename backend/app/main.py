"""
Backend Main - FastAPI uygulaması (middleware'ler dahil).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import auth, research, reports, admin
from backend.app.db.database import create_db_and_tables
from backend.app.core.middleware import (
    RateLimiterMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggerMiddleware,
)
from backend.app.core.config import settings

app = FastAPI(
    title="Nova Nexus Search API",
    description="Deep Research & Translation Platform — Production API",
    version=settings.VERSION,
)

# ─── Middleware Sırası (önemli: ilk eklenen en dışta çalışır) ──
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# ─── Routers ─────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
def read_root():
    return {
        "message": f"{settings.PROJECT_NAME} API is running",
        "version": settings.VERSION,
    }
