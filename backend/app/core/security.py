"""
Security - Şifre, JWT, Backup kodları. Üretim seviyesi.
"""
from datetime import datetime, timedelta
from typing import Any, Union, List, Tuple
import jwt
import bcrypt
import uuid
import re
import secrets
import hashlib
import json
from backend.app.core.config import settings


# ═══════════════════════════════════════════════════════════════
#  ŞİFRE
# ═══════════════════════════════════════════════════════════════

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
#  ŞİFRE GÜÇ DOĞRULAMA
# ═══════════════════════════════════════════════════════════════

class PasswordStrength:
    def __init__(self, score: int, feedback: List[str], is_valid: bool):
        self.score = score
        self.feedback = feedback
        self.is_valid = is_valid


def validate_password(password: str) -> PasswordStrength:
    feedback = []
    score = 0
    if len(password) >= settings.MIN_PASSWORD_LENGTH:
        score += 1
    else:
        feedback.append(f"En az {settings.MIN_PASSWORD_LENGTH} karakter olmalı")
    if re.search(r"[A-Z]", password):
        score += 1
    elif settings.REQUIRE_UPPERCASE:
        feedback.append("En az 1 büyük harf içermeli")
    if re.search(r"\d", password):
        score += 1
    elif settings.REQUIRE_DIGIT:
        feedback.append("En az 1 rakam içermeli")
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        score += 1
    elif settings.REQUIRE_SPECIAL_CHAR:
        feedback.append("En az 1 özel karakter içermeli (!@#$%...)")
    return PasswordStrength(score=score, feedback=feedback, is_valid=len(feedback) == 0)


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


# ═══════════════════════════════════════════════════════════════
#  JWT TOKEN (Access + Refresh)
# ═══════════════════════════════════════════════════════════════

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None, token_version: int = 0) -> Tuple[str, str]:
    """Access token üret. (token_str, jti) döndürür."""
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "exp": expire, "iat": datetime.utcnow(),
        "sub": str(subject), "jti": jti,
        "type": "access", "ver": token_version,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def create_refresh_token(subject: Union[str, Any], token_version: int = 0) -> Tuple[str, str]:
    """Refresh token üret. (token_str, jti) döndürür."""
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "exp": expire, "iat": datetime.utcnow(),
        "sub": str(subject), "jti": jti,
        "type": "refresh", "ver": token_version,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_token(token: str, expected_type: str = None) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            raise jwt.InvalidTokenError(f"Beklenen: {expected_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token süresi dolmuş")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Geçersiz token: {e}")


# ═══════════════════════════════════════════════════════════════
#  2FA BACKUP KODLARI
# ═══════════════════════════════════════════════════════════════

def _hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_backup_codes(count: int = 10) -> Tuple[List[str], str]:
    """
    10 adet tek kullanımlık backup kodu üretir.
    Returns: (plain_codes, hashed_json_string)
    """
    plain_codes = []
    hashed_codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()  # 8 karakter hex: "A1B2C3D4"
        code_formatted = f"{code[:4]}-{code[4:]}"  # "A1B2-C3D4"
        plain_codes.append(code_formatted)
        hashed_codes.append(_hash_backup_code(code_formatted))
    return plain_codes, json.dumps(hashed_codes)


def verify_backup_code(code: str, hashed_codes_json: str) -> Tuple[bool, str]:
    """
    Backup kodunu doğrular. Kullanıldıysa listeden siler.
    Returns: (is_valid, updated_hashed_json)
    """
    try:
        hashed_list = json.loads(hashed_codes_json)
    except (json.JSONDecodeError, TypeError):
        return False, hashed_codes_json or "[]"

    code_hash = _hash_backup_code(code.strip().upper())
    if code_hash in hashed_list:
        hashed_list.remove(code_hash)
        return True, json.dumps(hashed_list)
    return False, hashed_codes_json
