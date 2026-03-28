"""
Forgot Password View - Şifre sıfırlama onay ekranı.
"""
import flet as ft
from frontend.utils.theme import current_theme as th

def build_forgot_password_view(page: ft.Page, api_client, on_close) -> ft.Container:
    
    # ─── Durum ───
    step = [1]  # 1: E-posta giriş, 2: Token + Yeni Şifre giriş

    email_field = ft.TextField(
        label="Kayıtlı E-posta Adresiniz", 
        prefix_icon=ft.icons.EMAIL,
        border_color=th.border, focused_border_color=th.accent,
        color=th.text_main, bgcolor=th.surface_variant, border_radius=8, width=280
    )
    send_btn = ft.ElevatedButton(
        text="Sıfırlama Kodu Gönder", icon=ft.icons.SEND,
        bgcolor=th.accent_bg, color=th.accent, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    token_field = ft.TextField(
        label="Kurtarma Kodu (Token)", 
        prefix_icon=ft.icons.KEY, password=True,
        border_color=th.border, focused_border_color=th.accent,
        color=th.text_main, bgcolor=th.surface_variant, border_radius=8, width=280, visible=False
    )
    new_pw_field = ft.TextField(
        label="Yeni Şifre", 
        prefix_icon=ft.icons.LOCK, password=True, can_reveal_password=True,
        border_color=th.border, focused_border_color=th.accent,
        color=th.text_main, bgcolor=th.surface_variant, border_radius=8, width=280, visible=False
    )
    reset_btn = ft.ElevatedButton(
        text="Şifreyi Yenile", icon=ft.icons.LOCK_RESET,
        bgcolor=th.success_bg, color=th.success, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), visible=False
    )

    status_text = ft.Text("", size=12, text_align=ft.TextAlign.CENTER, color=th.text_dim)

    def handle_send(e):
        email = email_field.value.strip()
        if not email:
            status_text.value = "Lütfen e-posta girin."
            status_text.color = th.error
            page.update()
            return
        
        try:
            res = api_client.forgot_password(email)
            status_text.value = res.get("message", "Kod gönderildi. (Konsolu kontrol et)")
            status_text.color = th.success
            # Adım 2'ye geç
            email_field.disabled = True
            send_btn.visible = False
            token_field.visible = True
            new_pw_field.visible = True
            reset_btn.visible = True
        except Exception as ex:
            status_text.value = f"Hata: {ex}"
            status_text.color = th.error
        page.update()

    def handle_reset(e):
        token = token_field.value.strip()
        new_pw = new_pw_field.value.strip()
        if not token or not new_pw:
            status_text.value = "Lütfen tüm alanları doldurun."
            status_text.color = th.error
            page.update()
            return
        
        try:
            res = api_client.reset_password(token, new_pw)
            status_text.value = res.get("message", "Şifre değiştirildi! Giriş yapabilirsiniz.")
            status_text.color = th.success
            token_field.disabled = True
            new_pw_field.disabled = True
            reset_btn.disabled = True
        except Exception as ex:
            status_text.value = str(ex)
            status_text.color = th.error
        page.update()

    send_btn.on_click = handle_send
    reset_btn.on_click = handle_reset

    return ft.Container(
        padding=40, bgcolor=th.bg, border=ft.border.all(1, th.border), border_radius=12,
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.LOCK_RESET, color=th.accent, size=24),
                ft.Text("Şifre Sıfırlama", size=18, weight=ft.FontWeight.BOLD, color=th.text_main),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.icons.CLOSE, icon_color=th.text_muted, on_click=lambda e: on_close())
            ]),
            ft.Divider(color=th.border),
            ft.Text("Hesabınıza erişimi kaybettiyseniz parolanızı sıfırlayabilirsiniz.", size=12, color=th.text_dim),
            email_field,
            send_btn,
            token_field,
            new_pw_field,
            reset_btn,
            status_text
        ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
