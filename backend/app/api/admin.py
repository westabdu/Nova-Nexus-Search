"""
Admin API - Kullanıcı yönetimi (Sadece admin_email parametresi kontrol edilecek)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.app.db.database import get_session
from backend.app.models.user import User

router = APIRouter()

def require_admin(admin_email: str, session: Session):
    admin = session.exec(select(User).where(User.email == admin_email)).first()
    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Erişim engellendi: Yönetici yetkisi gerekli.")
    return admin

@router.get("/users")
async def list_users(
    admin_email: str,
    session: Session = Depends(get_session)
):
    require_admin(admin_email, session)
    users = session.exec(select(User)).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "quota_remaining": u.quota_remaining,
            "is_admin": u.is_admin,
            "created_at": u.created_at,
            "last_login": u.last_login,
        }
        for u in users
    ]

@router.post("/users/{user_id}/quota")
async def update_user_quota(
    user_id: int,
    quota: int,
    admin_email: str,
    session: Session = Depends(get_session)
):
    require_admin(admin_email, session)
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    user.quota_remaining = quota
    session.add(user)
    session.commit()
    return {"message": "Kota güncellendi", "quota": quota}

@router.post("/users/{user_id}/toggle-active")
async def toggle_user_status(
    user_id: int,
    admin_email: str,
    session: Session = Depends(get_session)
):
    admin = require_admin(admin_email, session)
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı devre dışı bırakamazsınız")
        
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    return {"message": f"Kullanıcı aktif: {user.is_active}", "is_active": user.is_active}
