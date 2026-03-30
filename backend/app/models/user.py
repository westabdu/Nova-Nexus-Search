"""
Models - User, Session, ResearchHistory + DTO'lar
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import json


# ═══════════════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════════════

class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    username: str
    is_active: bool = True
    quota_remaining: int = 10
    openrouter_api_key: Optional[str] = Field(default=None)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    api_key: Optional[str] = Field(default=None, unique=True, index=True)
    api_key_last_used: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reset_code: Optional[str] = None
    reset_code_expires: Optional[datetime] = None

    # 2FA
    totp_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = Field(default=None)
    totp_pending: bool = Field(default=False)
    backup_codes: Optional[str] = Field(default=None)  # JSON array of hashed codes

    # Brute-force
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)

    # Audit
    last_login: Optional[datetime] = Field(default=None)
    password_changed_at: Optional[datetime] = Field(default=None)

    # Token revocation: increment to invalidate all tokens
    token_version: int = Field(default=0)

    # Role
    is_admin: bool = Field(default=False)


# ═══════════════════════════════════════════════════════════════
#  SESSION (Aktif Oturumlar)
# ═══════════════════════════════════════════════════════════════

class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    token_jti: str = Field(index=True)          # JWT unique ID
    device_info: str = Field(default="Bilinmiyor")
    ip_address: str = Field(default="0.0.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    is_revoked: bool = Field(default=False)


# ═══════════════════════════════════════════════════════════════
#  RESEARCH HISTORY (Araştırma Geçmişi)
# ═══════════════════════════════════════════════════════════════

class ResearchHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    query: str
    depth: str = "medium"
    language: str = "tr"
    result_json: Optional[str] = Field(default=None)   # Full result as JSON
    source_count: int = Field(default=0)
    reliability_score: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_favorite: bool = Field(default=False)
    tags: Optional[str] = Field(default=None)           # comma-separated tags


# ═══════════════════════════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════════════════════════

class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    api_key: Optional[str] = None
    api_key_last_used: Optional[datetime] = None
    totp_enabled: bool = False
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_admin: bool = False
    openrouter_api_key: Optional[str] = None


class TOTPSetupResponse(SQLModel):
    qr_code_base64: str
    secret: str
    otpauth_url: str
    backup_codes: List[str] = []   # Plain text codes (shown only once)


class PasswordChangeRequest(SQLModel):
    old_password: str
    new_password: str


class SessionResponse(SQLModel):
    id: int
    device_info: str
    ip_address: str
    created_at: datetime
    is_current: bool = False


class ResearchHistoryResponse(SQLModel):
    id: int
    query: str
    depth: str
    language: str
    source_count: int
    reliability_score: int
    created_at: datetime
    is_favorite: bool
    tags: Optional[str] = None
