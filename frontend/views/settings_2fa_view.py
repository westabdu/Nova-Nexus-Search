"""
2FA Settings View - Google Authenticator kurulumu, yönetim paneli ve Yedek kodları (Tema Destekli)
"""
import flet as ft
from loguru import logger
from frontend.utils.theme import current_theme as th


def build_2fa_panel(page: ft.Page, api_client, on_close) -> ft.Container:
    email = api_client.user_info.get("email", "") if api_client.user_info else ""
    totp_enabled = api_client.user_info.get("totp_enabled", False) if api_client.user_info else False

    status_text = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)
    qr_image = ft.Image(visible=False, width=180, height=180)
    secret_text = ft.Text("", size=11, color=th.text_dim, selectable=True)
    
    code_field = ft.TextField(
        label="6 Haneli Doğrulama Kodu",
        prefix_icon=ft.icons.SECURITY,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=6,
        border_color=th.text_dim, focused_border_color=th.warning,
        color=th.text_main, bgcolor=th.surface, border_radius=10,
        visible=False, width=280,
    )
    
    setup_btn = ft.ElevatedButton(
        text="QR Kodu Oluştur", icon=ft.icons.QR_CODE_2,
        bgcolor=th.accent_bg, color=th.accent,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        visible=not totp_enabled,
    )
    verify_btn = ft.ElevatedButton(
        text="Etkinleştir", icon=ft.icons.CHECK_CIRCLE_OUTLINE,
        bgcolor=th.success_bg, color=th.success,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        visible=False,
    )
    
    backup_codes_text = ft.Text("", size=12, selectable=True, color=th.warning, text_align=ft.TextAlign.CENTER)
    backup_codes_container = ft.Container(
        content=ft.Column([
            ft.Text("⚠️ DİKKAT: Bu yedek kodları güvenli bir yere kaydedin. Bir daha gösterilmeyecektir!", color=th.error, size=11, weight="bold"),
            ft.Container(
                content=backup_codes_text,
                padding=10, bgcolor=th.surface_variant, border_radius=8,
                border=ft.border.all(1, th.border)
            )
        ], horizontal_alignment="center"),
        visible=False
    )

    disable_btn = ft.ElevatedButton(
        text="2FA Devre Dışı Bırak", icon=ft.icons.GPP_BAD,
        bgcolor=th.error_bg, color=th.error,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        visible=totp_enabled,
    )
    
    new_backup_btn = ft.ElevatedButton(
        text="Yedek Kodları Yenile", icon=ft.icons.REFRESH,
        bgcolor=th.accent_bg, color=th.accent,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        visible=totp_enabled,
    )
    
    regen_code_field = ft.TextField(
        label="Mevcut 2FA Kodu (Yenilemek İçin)",
        prefix_icon=ft.icons.SECURITY,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=6,
        border_color=th.border, focused_border_color=th.warning,
        color=th.text_main, bgcolor=th.surface, border_radius=10,
        visible=False, width=280,
    )
    do_regen_btn = ft.ElevatedButton(
        text="Kodları Değiştir", icon=ft.icons.SYNC,
        bgcolor=th.success_bg, color=th.success,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        visible=False,
    )

    def handle_setup(e):
        try:
            data = api_client.setup_2fa()
            qr_b64 = data.get("qr_code_base64")
            secret = data.get("secret")
            if qr_b64:
                qr_image.src_base64 = qr_b64
                qr_image.visible = True
            secret_text.value = f"Secret: {secret}"
            
            b_codes = data.get("backup_codes", [])
            if b_codes:
                backup_codes_text.value = "\\n".join(b_codes)
                backup_codes_container.visible = True

            code_field.visible = True
            verify_btn.visible = True
            setup_btn.visible = False
            status_text.value = "QR'ı taratın veya kodu uygulamaya ekleyin."
            status_text.color = th.text_main
        except Exception as ex:
            status_text.value = f"Kurulum hatası: {ex}"
            status_text.color = th.error
        page.update()

    def handle_verify(e):
        code = code_field.value.strip()
        if not code or len(code) != 6:
            status_text.value = "Lütfen 6 haneli kodu girin."
            status_text.color = th.warning
            page.update()
            return
            
        try:
            api_client.verify_2fa_setup(code=code)
            status_text.value = "✅ İki Aşamalı Doğrulama başarıyla aktifleştirildi!"
            status_text.color = th.success
            qr_image.visible = False
            secret_text.visible = False
            code_field.visible = False
            verify_btn.visible = False
            
            api_client.user_info["totp_enabled"] = True
            disable_btn.visible = True
        except Exception as ex:
            status_text.value = f"Geçersiz kod: {ex}"
            status_text.color = th.error
        page.update()

    def handle_disable(e):
        try:
            api_client.disable_2fa()
            status_text.value = "🚨 İki Aşamalı Doğrulama kapatıldı."
            status_text.color = th.warning
            disable_btn.visible = False
            setup_btn.visible = True
            backup_codes_container.visible = False
            api_client.user_info["totp_enabled"] = False
        except Exception as ex:
            status_text.value = f"Kapatılamadı: {ex}"
            status_text.color = th.error
        page.update()

    def prepare_regen(e):
        regen_code_field.visible = True
        do_regen_btn.visible = True
        new_backup_btn.visible = False
        page.update()

    def handle_regen(e):
        code = regen_code_field.value.strip()
        if not code or len(code) != 6:
            status_text.value = "Lütfen mevcut 2FA kodunuzu girin."
            status_text.color = th.warning
            page.update()
            return
            
        try:
            data = api_client.regenerate_backup_codes(code)
            codes = data.get("backup_codes", [])
            backup_codes_text.value = "\\n".join(codes)
            backup_codes_container.visible = True
            status_text.value = "Yedek kodlar başarıyla yenilendi!"
            status_text.color = th.success
            regen_code_field.value = ""
            regen_code_field.visible = False
            do_regen_btn.visible = False
            new_backup_btn.visible = True
        except Exception as ex:
            status_text.value = f"Hata: {ex}"
            status_text.color = th.error
        page.update()

    setup_btn.on_click = handle_setup
    verify_btn.on_click = handle_verify
    disable_btn.on_click = handle_disable
    new_backup_btn.on_click = prepare_regen
    do_regen_btn.on_click = handle_regen

    return ft.Container(
        padding=40, bgcolor=th.bg, border=ft.border.all(1, th.border), border_radius=12,
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.SHIELD, color=th.accent, size=24),
                ft.Text("2FA Güvenlik Ayarları", size=18, weight=ft.FontWeight.BOLD, color=th.text_main),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.icons.CLOSE, icon_color=th.text_muted, on_click=lambda e: on_close())
            ]),
            ft.Divider(color=th.border),
            ft.Text(f"Hesabınız ({email}) için Güvenlik Kalkanı", size=12, color=th.text_dim),
            setup_btn,
            disable_btn,
            new_backup_btn,
            regen_code_field,
            do_regen_btn,
            qr_image,
            secret_text,
            code_field,
            verify_btn,
            backup_codes_container,
            status_text
        ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
