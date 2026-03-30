"""
Profile Panel - Sol sidebar'da kullanıcı bilgileri, kota, API key, oturumlar + Admin + Tema
NOT: 2FA ve Şifre yönetimi güvenlik nedeniyle Giriş (Auth) ekranına taşınmıştır.
"""
import flet as ft
from frontend.utils.i18n import t
from frontend.utils.theme import current_theme as th
from frontend.views.admin_view import build_admin_view
from loguru import logger


def build_profile_panel(page: ft.Page, api_client, lang: str) -> ft.Container:
    """Sol Menüde (Sidebar) gösterilecek profil bilgi paneli."""

    info = api_client.user_info or {}
    email = info.get("email", "?")
    username = info.get("username", email.split("@")[0])
    api_key_initial = info.get("api_key", "")
    quota = info.get("quota_remaining", 10)
    is_admin = info.get("is_admin", False)

    state = {
        "api_key": api_key_initial
    }

    initials = (username[:2] if username else "NN").upper()
    avatar = ft.Container(
        width=48, height=48, border_radius=24,
        bgcolor=th.surface_variant,
        border=ft.border.all(2, th.accent),
        content=ft.Text(initials, size=16, weight=ft.FontWeight.BOLD,
                        color=th.accent, text_align=ft.TextAlign.CENTER),
        alignment=ft.alignment.center,
    )

    # ─── API Key Yönetimi ─────────────────────────────────────────
    def get_display_key():
        k = state["api_key"]
        return k[:12] + "•••" if k and len(k) > 12 else (k or "Yok")

    api_key_text = ft.Text(get_display_key(), size=10, color=th.text_muted, selectable=True)
    api_key_msg = ft.Text("", size=10)

    def copy_api_key(e):
        if state["api_key"]:
            page.set_clipboard(state["api_key"])
            api_key_msg.value = "✓ Kopyalandı!"
            api_key_msg.color = th.success
            page.update()

    def handle_regen_api_key(e):
        try:
            res = api_client.regenerate_api_key()
            state["api_key"] = res.get("api_key")
            api_key_text.value = get_display_key()
            api_key_msg.value = "✓ Yenilendi!"
            api_key_msg.color = th.success
        except Exception as ex:
            api_key_msg.value = "Hata oluştu."
            api_key_msg.color = th.error
        page.update()

    def handle_revoke_api_key(e):
        try:
            api_client.revoke_api_key()
            state["api_key"] = None
            api_key_text.value = get_display_key()
            api_key_msg.value = "✓ İptal edildi."
            api_key_msg.color = th.warning
        except Exception:
            api_key_msg.value = "Hata."
            api_key_msg.color = th.error
        page.update()

    # ─── Diğer AI Modelleri için API Key ─────────────────────────────────────────
    openrouter_f = ft.TextField(value=info.get("openrouter_api_key", "") or "", hint_text="OpenRouter API Key (İsteğe Bağlı)", password=True, can_reveal_password=True, text_size=12, height=40, bgcolor="#10ffffff" if th.is_dark else "#0a000000", border_color=th.border)
    ai_msg = ft.Text("", size=10)

    def handle_save_ai(e):
        try:
            api_client.update_ai_keys(openrouter_f.value.strip())
            ai_msg.value = "✓ Kaydedildi!"
            ai_msg.color = th.success
        except Exception:
            ai_msg.value = "Hata oluştu."
            ai_msg.color = th.error
        page.update()

    ai_settings_section = ft.Column([
        ft.Divider(color=th.border, height=1),
        ft.Row([
            ft.Icon(ft.icons.SMART_TOY, size=14, color=th.text_dim),
            ft.Text("Kişisel AI Api Anahtarları", size=12, color=th.text_dim, weight=ft.FontWeight.W_600),
        ]),
        openrouter_f,
        ft.ElevatedButton(content=ft.Text("Anahtarları Kaydet", color="#fff"), bgcolor=th.success, height=32, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=handle_save_ai),
        ai_msg
    ], spacing=8, visible=False)

    def toggle_ai_section(e):
        ai_settings_section.visible = not ai_settings_section.visible
        page.update()

    # ─── Kota Progress ────────────────────────────────────────────
    quota_pct = max(0, min(1.0, quota / 10))
    quota_color = th.success if quota > 5 else th.warning if quota > 2 else th.error

    # ─── Tema (Gece / Gündüz) ────────────────────────────────────────────
    def handle_theme_toggle(e):
        th.is_dark = not th.is_dark
        th.update()
        page.theme_mode = ft.ThemeMode.DARK if th.is_dark else ft.ThemeMode.LIGHT
        
        e.control.icon = ft.icons.DARK_MODE if not th.is_dark else ft.icons.LIGHT_MODE
        e.control.icon_color = th.warning if not th.is_dark else th.accent
        page.update()
        
        page.snack_bar = ft.SnackBar(ft.Text("Tema değişti. Ekranı yenileyin (F5).", color="#ffffff"), bgcolor=th.success, duration=3000)
        page.snack_bar.open = True
        page.update()

    # ─── Oturum Yönetimi ─────────────────────────────────────────
    sessions_list = ft.Column(spacing=4)
    sessions_msg = ft.Text("", size=10)

    def load_sessions():
        sessions_list.controls.clear()
        try:
            sessions = api_client.list_sessions()
            for s in sessions[:5]:
                dt_str = s.get("created_at", "").replace("T", " ")[:16]
                row = ft.Container(
                    bgcolor=th.surface_variant, padding=8, border_radius=6,
                    content=ft.Column([
                        ft.Text(f"{s.get('device_info', '?')} - {s.get('ip_address', '?')}", size=11, color=th.text_main, weight=ft.FontWeight.W_600),
                        ft.Text(f"Giriş: {dt_str}", size=10, color=th.text_muted),
                    ], spacing=2)
                )
                sessions_list.controls.append(row)
        except Exception as e:
            sessions_msg.value = "Oturumlar yüklenemedi."
            sessions_msg.color = th.error

    def handle_revoke_all(e):
        try:
            api_client.revoke_all_sessions()
            sessions_msg.value = "✅ Çıkış yapıldı. (Mevcut hariç)"
            sessions_msg.color = th.success
            load_sessions()
        except Exception as ex:
            sessions_msg.value = "Hata oluştu."
            sessions_msg.color = th.error
        page.update()

    sessions_section = ft.Column([
        ft.Divider(color=th.border, height=1),
        ft.Row([
            ft.Icon(ft.icons.DEVICES, size=14, color=th.text_dim),
            ft.Text("Aktif Oturumlar", size=12, color=th.text_dim, weight=ft.FontWeight.W_600),
        ]),
        sessions_list,
        ft.TextButton("Tüm Diğer Cihazlardan Çık", icon=ft.icons.LOGOUT, icon_color=th.error, style=ft.ButtonStyle(color=th.error), on_click=handle_revoke_all),
        sessions_msg
    ], spacing=8, visible=False)

    def toggle_sessions_section(e):
        sessions_section.visible = not sessions_section.visible
        if sessions_section.visible:
            load_sessions()
        page.update()

    # ─── Admin Paneli Trigger ─────────────────────────────────────────
    admin_btn = ft.Container(visible=False)
    if is_admin:
        def _open_admin(e):
            overlay = build_admin_view(page, api_client, lambda: page.overlay.remove(overlay) or page.update())
            page.overlay.append(overlay)
            page.update()
            
        admin_btn = ft.TextButton(
            "🛡️ Yönetim Paneli", icon=ft.icons.SHIELD, icon_color=th.warning, 
            style=ft.ButtonStyle(color=th.text_main), on_click=_open_admin
        )


    return ft.Container(
        width=260,
        padding=16,
        bgcolor=th.surface,
        border=ft.border.all(1, th.border),
        border_radius=12,
        content=ft.Column([
            ft.Row([
                avatar, 
                ft.Column([
                    ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=th.text_main),
                    ft.Text(email, size=11, color=th.text_muted),
                ], spacing=2),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.LIGHT_MODE if th.is_dark else ft.icons.DARK_MODE, 
                    icon_color=th.accent if th.is_dark else th.warning, 
                    icon_size=20, on_click=handle_theme_toggle, tooltip="Açık/Koyu Mod"
                )
            ], spacing=10),

            ft.Divider(color=th.border, height=1),

            ft.Text("API Anahtarı", size=11, color=th.text_dim),
            ft.Row([
                api_key_text,
                ft.IconButton(icon=ft.icons.COPY, icon_size=14, icon_color=th.text_muted, on_click=copy_api_key, tooltip="Kopyala"),
            ], spacing=2),
            ft.Row([
                ft.TextButton("Yenile", icon=ft.icons.AUTORENEW, icon_color=th.accent, style=ft.ButtonStyle(color=th.accent), on_click=handle_regen_api_key),
                ft.TextButton("İptal", icon=ft.icons.BLOCK, icon_color=th.error, style=ft.ButtonStyle(color=th.error), on_click=handle_revoke_api_key),
            ], spacing=0, alignment=ft.MainAxisAlignment.START),
            api_key_msg,

            ft.Divider(color=th.border, height=1),

            ft.Text(f"{t('quota_label', lang)}", size=11, color=th.text_dim),
            ft.Row([
                ft.Text(f"{quota}/10", size=14, weight=ft.FontWeight.BOLD, color=quota_color),
                ft.Text("araştırma", size=11, color=th.text_dim),
            ], spacing=4),
            ft.ProgressBar(value=quota_pct, color=quota_color, bgcolor=th.surface_variant, height=4),

            ft.Divider(color=th.border, height=1),

            admin_btn,
            ft.TextButton("🤖 Ayarlar: AI API", icon=ft.icons.SMART_TOY, style=ft.ButtonStyle(color=th.text_dim), on_click=toggle_ai_section),
            ai_settings_section,
            ft.TextButton("💻 Oturumlar", icon=ft.icons.DEVICES, style=ft.ButtonStyle(color=th.text_dim), on_click=toggle_sessions_section),
            sessions_section,
            
            ft.Container(expand=True),
            ft.Text("⚠️ 2FA & Şifre Yönetimi, giriş sayfasındaki 'Şifremi Unuttum' paneline taşınmıştır.", size=10, color=th.text_dim, text_align=ft.TextAlign.CENTER, italic=True)

        ], spacing=8, scroll=ft.ScrollMode.ADAPTIVE),
    )
