"""
API Client - Backend ile HTTP + Token yönetimi.
Phase 1 Güncellemeleri ile (Session, API Key, History, Backup Codes).
"""
import httpx
from typing import Optional, List
from loguru import logger

BASE_URL = "http://127.0.0.1:8000"


class APIClient:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token_str: Optional[str] = None
        self.user_info: Optional[dict] = None

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    def _try_refresh(self):
        if not self.refresh_token_str:
            return False
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{BASE_URL}/api/auth/refresh-token",
                    params={"token": self.refresh_token_str},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.access_token = data.get("access_token", "")
                    logger.info("Token yenilendi (refresh)")
                    return True
        except Exception:
            pass
        return False

    def _email(self) -> str:
        return self.user_info.get("email", "") if self.user_info else ""

    # ─── Auth ────────────────────────────────────────────────────
    def login(self, email: str, password: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/login/access-token",
                data={"username": email, "password": password},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("requires_2fa"):
                self.access_token = data.get("access_token", "")
                self.refresh_token_str = data.get("refresh_token", "")
                self.user_info = data.get("user", {"email": email})
            return data

    def register(self, email: str, password: str, username: str, groq_key: str = "", gemini_key: str = "", deepseek_key: str = "") -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": email, "password": password, "username": username,
                    "groq_api_key": groq_key or None,
                    "gemini_api_key": gemini_key or None,
                    "deepseek_api_key": deepseek_key or None
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self.user_info = data
            return data

    def logout(self):
        self.access_token = None
        self.refresh_token_str = None
        self.user_info = None

    def change_password(self, old_password: str, new_password: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/change-password",
                params={"user_email": self._email()},
                json={"old_password": old_password, "new_password": new_password},
            )
            resp.raise_for_status()
            return resp.json()

    def update_ai_keys(self, groq_key: str, gemini_key: str, deepseek_key: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/update-ai-keys",
                json={
                    "user_email": self._email(),
                    "groq_api_key": groq_key or None,
                    "gemini_api_key": gemini_key or None,
                    "deepseek_api_key": deepseek_key or None
                },
            )
            resp.raise_for_status()
            # Update local cache
            if self.user_info:
                self.user_info["groq_api_key"] = groq_key or None
                self.user_info["gemini_api_key"] = gemini_key or None
                self.user_info["deepseek_api_key"] = deepseek_key or None
            return resp.json()

    # ─── 2FA & Backup Codes ──────────────────────────────────────
    def setup_2fa(self, email: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{BASE_URL}/api/auth/2fa/setup", params={"user_email": email})
            resp.raise_for_status()
            return resp.json()

    def verify_2fa_setup(self, email: str, code: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/2fa/verify-setup",
                params={"user_email": email, "code": code},
            )
            resp.raise_for_status()
            return resp.json()

    def verify_2fa_login(self, email: str, code: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/2fa/login-verify",
                params={"user_email": email, "code": code},
            )
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get("access_token", "")
            self.refresh_token_str = data.get("refresh_token", "")
            self.user_info = data.get("user", {"email": email})
            return data

    def disable_2fa(self, email: str, code: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/2fa/disable",
                params={"user_email": email, "code": code},
            )
            resp.raise_for_status()
            return resp.json()

    def regenerate_backup_codes(self, code: str) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/2fa/regenerate-backup-codes",
                params={"user_email": self._email(), "code": code},
            )
            resp.raise_for_status()
            return resp.json()

    # ─── Oturum Yönetimi (Sessions) ──────────────────────────────
    def list_sessions(self) -> list:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{BASE_URL}/api/auth/sessions",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            return resp.json()

    def revoke_session(self, session_id: int) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/revoke-session/{session_id}",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            return resp.json()

    def revoke_all_sessions(self) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/revoke-all-sessions",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            return resp.json()

    # ─── API Key Yönetimi ────────────────────────────────────────
    def regenerate_api_key(self) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/regenerate-api-key",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            data = resp.json()
            if self.user_info:
                self.user_info["api_key"] = data.get("api_key")
            return data

    def revoke_api_key(self) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/revoke-api-key",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            if self.user_info:
                self.user_info["api_key"] = None
            return resp.json()

    # ─── Araştırma & Geçmiş (History) ────────────────────────────
    def get_quota(self) -> int:
        if not self.user_info: return 0
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/research/check-quota",
                params={"user_email": self._email()},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json().get("quota_remaining", 0)
        return 0

    def start_research_session(self) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{BASE_URL}/api/research/start", headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    def cancel_research(self, session_id: str) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{BASE_URL}/api/research/cancel/{session_id}")
            resp.raise_for_status()
            return resp.json()

    def get_research_history(self) -> list:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{BASE_URL}/api/auth/research-history",
                params={"user_email": self._email()},
            )
            resp.raise_for_status()
            return resp.json()

    def get_research_detail(self, history_id: int) -> dict:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{BASE_URL}/api/auth/research-history/{history_id}")
            resp.raise_for_status()
            return resp.json()

    def toggle_history_favorite(self, history_id: int) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{BASE_URL}/api/auth/research-history/{history_id}/favorite")
            resp.raise_for_status()
            return resp.json()

    def delete_history(self, history_id: int) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.delete(f"{BASE_URL}/api/auth/research-history/{history_id}")
            resp.raise_for_status()
            return resp.json()

    def save_report(self, research_result: dict, formats: list) -> dict:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{BASE_URL}/api/reports/save",
                json={"research_result": research_result, "formats": formats},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    def update_history_tags(self, history_id: int, tags: str) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/research-history/{history_id}/tags",
                params={"tags": tags},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ─── Şifre Sıfırlama (Forgot / Reset) ────────────────────────
    def forgot_password(self, email: str) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{BASE_URL}/api/auth/forgot-password", params={"email": email})
            resp.raise_for_status()
            return resp.json()

    def reset_password(self, token: str, new_password: str) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/reset-password",
                params={"token": token, "new_password": new_password}
            )
            resp.raise_for_status()
            return resp.json()

    # ─── Admin İşlemleri ─────────────────────────────────────────
    def get_all_users(self) -> list:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{BASE_URL}/api/admin/users", 
                params={"admin_email": self.user_info.get("email", "") if self.user_info else ""},
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    def update_user_quota(self, user_id: int, quota: int) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/admin/users/{user_id}/quota",
                params={"quota": quota, "admin_email": self.user_info.get("email", "") if self.user_info else ""},
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    def toggle_user_status(self, user_id: int) -> dict:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{BASE_URL}/api/admin/users/{user_id}/toggle-active",
                params={"admin_email": self.user_info.get("email", "") if self.user_info else ""},
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()
