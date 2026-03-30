"""
Auth API — Kayıt, Giriş, 2FA+Backup, Oturum Yönetimi, API Key, Şifre Değiştirme, E-posta ile Şifre Sıfırlama (6 Haneli Kod)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from backend.app.db.database import get_session
from backend.app.models.user import (
    User, UserCreate, UserResponse, TOTPSetupResponse,
    PasswordChangeRequest, UserSession, SessionResponse,
    ResearchHistory, ResearchHistoryResponse,
)
from backend.app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, validate_password, validate_email,
    generate_backup_codes, verify_backup_code,
)
from backend.app.core.config import settings
import secrets, pyotp, qrcode, io, base64, json, logging, smtplib, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Yardımcılar ──────────────────────────────────────────────────

def _qr_base64(otpauth_url: str) -> str:
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00d4ff", back_color="#111827")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _check_lockout(user: User):
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
        raise HTTPException(status_code=423, detail=f"Hesap kilitli. {remaining} dk sonra deneyin.")


def _record_failed(user: User, session: Session):
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
        user.failed_login_attempts = 0
    session.add(user)
    session.commit()


def _record_success(user: User, session: Session):
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()


def _create_session_record(user: User, jti: str, request: Request, session: Session):
    """Oturum kaydı oluştur."""
    device = "Bilinmiyor"
    if request:
        ua = request.headers.get("user-agent", "")
        if "Windows" in ua:
            device = "Windows"
        elif "Mac" in ua:
            device = "macOS"
        elif "Linux" in ua:
            device = "Linux"
        elif "Android" in ua:
            device = "Android"
        elif "iPhone" in ua:
            device = "iPhone"
    ip = request.client.host if request and request.client else "127.0.0.1"
    sess_record = UserSession(
        user_id=user.id, token_jti=jti,
        device_info=device, ip_address=ip,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(sess_record)
    session.commit()


def _build_token_response(user: User, session: Session, request: Request = None) -> dict:
    _record_success(user, session)
    access_token, access_jti = create_access_token(subject=user.id, token_version=user.token_version)
    refresh_token, refresh_jti = create_refresh_token(subject=user.id, token_version=user.token_version)
    if request:
        _create_session_record(user, refresh_jti, request, session)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "requires_2fa": False,
        "user": {
            "id": user.id, "email": user.email, "username": user.username,
            "api_key": user.api_key, "totp_enabled": user.totp_enabled,
            "quota_remaining": user.quota_remaining, "is_admin": user.is_admin,
            "openrouter_api_key": user.openrouter_api_key,
        },
    }


def send_reset_email_smtp(to_email: str, code: str) -> bool:
    """SMTP (Gmail) ile şifre sıfırlama e-postası gönder (6 haneli kod)"""
    
    subject = "Nova Nexus Search - Şifre Sıfırlama"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; background: #0A0A0F; padding: 40px;">
        <div style="max-width: 500px; margin: 0 auto; background: #1A1A2E; border-radius: 16px; padding: 30px; border: 1px solid #00F0FF;">
            <h1 style="color: #00F0FF; text-align: center;">🔐 Nova Nexus</h1>
            <h2 style="color: #FFFFFF; text-align: center;">Şifre Sıfırlama Talebi</h2>
            <p style="color: #A0A0B0;">Merhaba,</p>
            <p style="color: #A0A0B0;">Şifre sıfırlama talebinde bulundunuz. Aşağıdaki 6 haneli kodu kullanarak yeni şifre belirleyebilirsiniz:</p>
            <div style="background: #0A0A0F; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <code style="color: #00F0FF; font-size: 28px; font-weight: bold; letter-spacing: 4px;">{code}</code>
            </div>
            <p style="color: #A0A0B0; font-size: 12px;">Bu kod <strong>15 dakika</strong> geçerlidir.</p>
            <p style="color: #A0A0B0;">Eğer bu talebi siz yapmadıysanız, bu e-postayı dikkate almayın.</p>
            <hr style="border-color: #2A2A38;">
            <p style="color: #A0A0B0; font-size: 11px; text-align: center;">Nova Nexus Search - Bilginin Sınırlarını Keşfedin</p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ SMTP ile e-posta gönderildi: {to_email} -> Kod: {code}")
        return True
    except Exception as e:
        logger.error(f"❌ SMTP e-posta hatası: {e}")
        return False


# ══════════════════════════════════════════════════════════════
#  KAYIT
# ══════════════════════════════════════════════════════════════

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Geçersiz e-posta formatı.")
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")
    strength = validate_password(user.password)
    if not strength.is_valid:
        raise HTTPException(status_code=400, detail="Şifre zayıf: " + " | ".join(strength.feedback))

    db_user = User(
        email=user.email, username=user.username,
        hashed_password=get_password_hash(user.password),
        quota_remaining=10, is_active=True,
        api_key="sk-nova-" + secrets.token_hex(16),
        totp_enabled=False, totp_secret=None, totp_pending=False,
        backup_codes=None, failed_login_attempts=0, locked_until=None,
        last_login=None, password_changed_at=datetime.utcnow(),
        token_version=0, is_admin=False,
        openrouter_api_key=user.openrouter_api_key,
        reset_code=None, reset_code_expires=None,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


# ══════════════════════════════════════════════════════════════
#  GİRİŞ
# ══════════════════════════════════════════════════════════════

@router.post("/login/access-token")
def login_access_token(
    request: Request,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre hatalı.")
    _check_lockout(user)
    if not verify_password(form_data.password, user.hashed_password):
        _record_failed(user, session)
        remaining = settings.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
        if remaining > 0:
            raise HTTPException(status_code=400, detail=f"Şifre hatalı. Kalan: {remaining}")
        raise HTTPException(status_code=423, detail=f"Hesap {settings.LOCKOUT_MINUTES} dk kilitlendi.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Hesap aktif değil.")

    if user.totp_enabled:
        temp_token, _ = create_access_token(subject=f"2fa:{user.email}", expires_delta=timedelta(minutes=5))
        return {"requires_2fa": True, "temp_token": temp_token}

    return _build_token_response(user, session, request)


# ══════════════════════════════════════════════════════════════
#  REFRESH TOKEN
# ══════════════════════════════════════════════════════════════

@router.post("/refresh-token")
def refresh_token_endpoint(token: str, session: Session = Depends(get_session)):
    try:
        payload = decode_token(token, expected_type="refresh")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    user = session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı.")
    if payload.get("ver", 0) != user.token_version:
        raise HTTPException(status_code=401, detail="Token iptal edilmiş.")
    # Oturum revoke edilmiş mi?
    jti = payload.get("jti", "")
    sess_record = session.exec(select(UserSession).where(UserSession.token_jti == jti)).first()
    if sess_record and sess_record.is_revoked:
        raise HTTPException(status_code=401, detail="Oturum sonlandırılmış.")
    new_access, _ = create_access_token(subject=user.id, token_version=user.token_version)
    return {"access_token": new_access, "token_type": "bearer"}


# ══════════════════════════════════════════════════════════════
#  ŞİFRE DEĞİŞTİRME
# ══════════════════════════════════════════════════════════════

@router.post("/change-password")
def change_password(user_email: str, req: PasswordChangeRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı.")
    strength = validate_password(req.new_password)
    if not strength.is_valid:
        raise HTTPException(status_code=400, detail="Yeni şifre zayıf: " + " | ".join(strength.feedback))
    if verify_password(req.new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Yeni şifre eskiyle aynı olamaz.")

    user.hashed_password = get_password_hash(req.new_password)
    user.password_changed_at = datetime.utcnow()
    # Tüm oturumları iptal et
    user.token_version += 1
    sessions = session.exec(select(UserSession).where(UserSession.user_id == user.id, UserSession.is_revoked == False)).all()
    for s in sessions:
        s.is_revoked = True
        session.add(s)
    session.add(user)
    session.commit()
    return {"message": "✅ Şifre değiştirildi. Tüm oturumlar sonlandırıldı."}


# ══════════════════════════════════════════════════════════════
#  ŞİFRE GÜÇ KONTROLÜ
# ══════════════════════════════════════════════════════════════

@router.post("/check-password-strength")
def check_password_strength(password: str):
    s = validate_password(password)
    return {"score": s.score, "is_valid": s.is_valid, "feedback": s.feedback}


# ══════════════════════════════════════════════════════════════
#  2FA KURULUM + BACKUP KODLARI
# ══════════════════════════════════════════════════════════════

@router.post("/2fa/setup", response_model=TOTPSetupResponse)
def setup_2fa(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA zaten etkin.")

    secret = pyotp.random_base32()
    plain_codes, hashed_json = generate_backup_codes(10)

    user.totp_secret = secret
    user.totp_pending = True
    user.backup_codes = hashed_json
    session.add(user)
    session.commit()

    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=user.email, issuer_name="Nova Nexus Search")
    return TOTPSetupResponse(
        qr_code_base64=_qr_base64(otpauth_url),
        secret=secret, otpauth_url=otpauth_url,
        backup_codes=plain_codes,
    )


@router.post("/2fa/verify-setup")
def verify_2fa_setup(user_email: str, code: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=404, detail="Önce /2fa/setup çağrısı yapın.")
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Geçersiz kod.")
    user.totp_enabled = True
    user.totp_pending = False
    session.add(user)
    session.commit()
    return {"message": "✅ 2FA etkinleştirildi."}


@router.post("/2fa/login-verify")
def verify_2fa_login(user_email: str, code: str, request: Request, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA etkin değil.")
    _check_lockout(user)

    totp = pyotp.TOTP(user.totp_secret)
    if totp.verify(code, valid_window=1):
        return _build_token_response(user, session, request)

    # Backup kodu dene
    if user.backup_codes:
        valid, updated = verify_backup_code(code, user.backup_codes)
        if valid:
            user.backup_codes = updated
            session.add(user)
            session.commit()
            return _build_token_response(user, session, request)

    _record_failed(user, session)
    raise HTTPException(status_code=400, detail="Geçersiz kod.")


@router.post("/2fa/disable")
def disable_2fa(user_email: str, code: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA devre dışı.")
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Geçersiz kod.")
    user.totp_enabled = False
    user.totp_secret = None
    user.totp_pending = False
    user.backup_codes = None
    session.add(user)
    session.commit()
    return {"message": "2FA devre dışı bırakıldı."}


@router.post("/2fa/regenerate-backup-codes")
def regenerate_backup_codes(user_email: str, code: str, session: Session = Depends(get_session)):
    """Mevcut TOTP koduyla doğrulayıp yeni backup kodları üretir."""
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA etkin değil.")
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Geçersiz kod.")
    plain_codes, hashed_json = generate_backup_codes(10)
    user.backup_codes = hashed_json
    session.add(user)
    session.commit()
    return {"backup_codes": plain_codes, "message": "Yeni kodlar üretildi. Eski kodlar artık geçersiz."}


# ══════════════════════════════════════════════════════════════
#  OTURUM YÖNETİMİ
# ══════════════════════════════════════════════════════════════

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    records = session.exec(
        select(UserSession)
        .where(UserSession.user_id == user.id, UserSession.is_revoked == False)
        .order_by(UserSession.created_at.desc())
    ).all()
    return [SessionResponse(
        id=r.id, device_info=r.device_info, ip_address=r.ip_address,
        created_at=r.created_at, is_current=False,
    ) for r in records]


@router.post("/revoke-session/{session_id}")
def revoke_session(session_id: int, user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    record = session.get(UserSession, session_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı.")
    record.is_revoked = True
    session.add(record)
    session.commit()
    return {"message": "Oturum sonlandırıldı."}


@router.post("/revoke-all-sessions")
def revoke_all_sessions(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    user.token_version += 1
    records = session.exec(
        select(UserSession).where(UserSession.user_id == user.id, UserSession.is_revoked == False)
    ).all()
    for r in records:
        r.is_revoked = True
        session.add(r)
    session.add(user)
    session.commit()
    return {"message": f"{len(records)} oturum sonlandırıldı."}


# ══════════════════════════════════════════════════════════════
#  API KEY YÖNETİMİ
# ══════════════════════════════════════════════════════════════

@router.post("/regenerate-api-key")
def regenerate_api_key(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    new_key = "sk-nova-" + secrets.token_hex(16)
    user.api_key = new_key
    user.api_key_last_used = None
    session.add(user)
    session.commit()
    return {"api_key": new_key, "message": "Yeni API anahtarı oluşturuldu."}


@router.post("/revoke-api-key")
def revoke_api_key(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    user.api_key = None
    session.add(user)
    session.commit()
    return {"message": "API anahtarı iptal edildi."}

class AIKeyUpdate(BaseModel):
    user_email: str
    openrouter_api_key: Optional[str] = None

@router.post("/update-ai-keys")
def update_ai_keys(keys: AIKeyUpdate, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == keys.user_email)).first()
    if not user: raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    user.openrouter_api_key = keys.openrouter_api_key
    session.add(user)
    session.commit()
    return {"message": "AI API Anahtarları güncellendi."}


# ══════════════════════════════════════════════════════════════
#  ARAŞTIRMA GEÇMİŞİ
# ══════════════════════════════════════════════════════════════

@router.get("/research-history", response_model=List[ResearchHistoryResponse])
def get_research_history(user_email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    records = session.exec(
        select(ResearchHistory)
        .where(ResearchHistory.user_id == user.id)
        .order_by(ResearchHistory.created_at.desc())
    ).all()
    return records


@router.get("/research-history/{history_id}")
def get_research_detail(history_id: int, session: Session = Depends(get_session)):
    record = session.get(ResearchHistory, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    result = json.loads(record.result_json) if record.result_json else {}
    return {"record": record, "result": result}


@router.post("/research-history/{history_id}/favorite")
def toggle_favorite(history_id: int, session: Session = Depends(get_session)):
    record = session.get(ResearchHistory, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    record.is_favorite = not record.is_favorite
    session.add(record)
    session.commit()
    return {"is_favorite": record.is_favorite}


@router.delete("/research-history/{history_id}")
def delete_history(history_id: int, session: Session = Depends(get_session)):
    record = session.get(ResearchHistory, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    session.delete(record)
    session.commit()
    return {"message": "Silindi."}


@router.post("/research-history/{history_id}/tags")
def update_history_tags(history_id: int, tags: str, session: Session = Depends(get_session)):
    record = session.get(ResearchHistory, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    record.tags = tags
    session.add(record)
    session.commit()
    return {"message": "Etiketler güncellendi", "tags": record.tags}


# ══════════════════════════════════════════════════════════════
#  ŞİFRE SIFIRLAMA (6 Haneli Kod ile)
# ══════════════════════════════════════════════════════════════

@router.post("/forgot-password")
def forgot_password(email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return {"message": "Eğer e-posta sistemde kayıtlıysa, şifre sıfırlama kodu gönderdik."}
    
    # 6 haneli rastgele kod üret (100000 - 999999)
    reset_code = str(random.randint(100000, 999999))
    
    # Kodu veritabanında sakla (15 dakika geçerli)
    user.reset_code = reset_code
    user.reset_code_expires = datetime.utcnow() + timedelta(minutes=15)
    session.add(user)
    session.commit()
    
    # SMTP ile e-posta gönder
    success = send_reset_email_smtp(user.email, reset_code)
    
    if success:
        logger.info(f"📧 Şifre sıfırlama kodu gönderildi: {user.email} -> {reset_code}")
        return {"message": "Şifre sıfırlama kodu e-posta adresinize gönderildi. Lütfen spam klasörünü de kontrol edin."}
    else:
        logger.error(f"❌ E-posta gönderilemedi: {user.email}")
        return {"message": "E-posta gönderilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin."}


@router.post("/reset-password")
def reset_password(
    email: str = Form(...),
    code: str = Form(...),
    new_password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    
    # Kodu kontrol et
    if user.reset_code != code:
        raise HTTPException(status_code=400, detail="Geçersiz veya hatalı kod.")
    
    if user.reset_code_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş. Lütfen yeni kod isteyin.")
    
    # Şifre gücünü kontrol et
    strength = validate_password(new_password)
    if not strength.is_valid:
        raise HTTPException(status_code=400, detail="Yeni şifre zayıf: " + " | ".join(strength.feedback))
    
    # Şifreyi güncelle
    user.hashed_password = get_password_hash(new_password)
    user.token_version += 1
    user.reset_code = None
    user.reset_code_expires = None
    
    # Tüm aktif oturumları kapat
    active_sessions = session.exec(select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.is_revoked == False
    )).all()
    for s in active_sessions:
        s.is_revoked = True
        session.add(s)
    
    session.add(user)
    session.commit()
    
    return {"message": "Şifreniz başarıyla sıfırlandı. Lütfen yeni şifrenizle giriş yapın."}