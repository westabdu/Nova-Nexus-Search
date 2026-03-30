"""
Config - Uygulama ayarları ve güvenlik sabitleri.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Nova Nexus Search"
    VERSION: str = "2.0.0"

    # ─── JWT ─────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30           # 30 dakika
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7              # 7 gün

    # ─── Brute-force Koruması ────────────────────────────────────
    MAX_LOGIN_ATTEMPTS: int = 5                     # Peş peşe max yanlış deneme
    LOCKOUT_MINUTES: int = 15                       # Kilitleme süresi (dakika)

    # ─── Şifre Politikası ────────────────────────────────────────
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_DIGIT: bool = True
    REQUIRE_SPECIAL_CHAR: bool = True

    # ─── Rate Limiting ───────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30                 # IP başına dakikada max istek

    # ─── API Keys ────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # ─── SMTP E-posta (Gmail) ───────────────────────────────────
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")


settings = Settings()