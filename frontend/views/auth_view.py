"""
Auth View - macOS x Windows 11 Yarı Saydam (Glassmorphism) Estetiği
Nova Nexus v3.0 Premium Giriş Arayüzü
"""
import flet as ft
import re
from frontend.utils.i18n import t
from frontend.utils.theme import current_theme as th
from frontend.views.forgot_password_view import build_forgot_password_view
from loguru import logger

def _password_score(pw: str) -> tuple:
    score = 0
    if len(pw) >= 8: score += 1
    if re.search(r"[A-Z]", pw): score += 1
    if re.search(r"\d", pw): score += 1
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", pw): score += 1
    labels = ["", "Zayıf", "Orta", "İyi", "Güçlü"]
    colors = [th.border, th.error, th.warning, th.accent, th.success]
    return score, labels[score], colors[score]

def build_auth_view(page: ft.Page, api_client, on_login_success, current_lang: str = "tr"):

    is_register   = [False]
    pending_2fa   = [False]
    pending_email = [""]

    forgot_overlay = ft.Container(visible=False, alignment=ft.alignment.center)

    def _close_forgot():
        forgot_overlay.visible = False
        page.update()

    def _open_forgot(e):
        forgot_overlay.content = build_forgot_password_view(page, api_client, _close_forgot)
        forgot_overlay.visible = True
        page.update()

    # Yarı saydam arka plan (Windows Mica / macOS Glass) için TextField stili
    _field_style = dict(
        border=ft.InputBorder.NONE,
        color=th.text_main,
        bgcolor="#10ffffff" if th.is_dark else "#0a000000",
        border_radius=12,
        content_padding=ft.padding.all(16),
        text_size=14,
    )

    email_field = ft.TextField(hint_text="E-posta", prefix_icon=ft.icons.EMAIL_ROUNDED, **_field_style)
    password_field = ft.TextField(hint_text="Şifre", prefix_icon=ft.icons.LOCK_ROUNDED, password=True, can_reveal_password=True, **_field_style)
    username_field = ft.TextField(hint_text="Kullanıcı Adı", prefix_icon=ft.icons.PERSON_ROUNDED, visible=False, **_field_style)
    groq_key_field = ft.TextField(hint_text="Groq API Key (İsteğe Bağlı)", prefix_icon=ft.icons.KEY, visible=False, password=True, can_reveal_password=True, **_field_style)
    gemini_key_field = ft.TextField(hint_text="Gemini API Key (İsteğe Bağlı)", prefix_icon=ft.icons.KEY, visible=False, password=True, can_reveal_password=True, **_field_style)
    deepseek_key_field = ft.TextField(hint_text="DeepSeek API Key (İsteğe Bağlı)", prefix_icon=ft.icons.KEY, visible=False, password=True, can_reveal_password=True, **_field_style)
    
    totp_field = ft.TextField(
        hint_text="Google Auth (6 Hane)", prefix_icon=ft.icons.SECURITY_ROUNDED,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=6, visible=False,
        border_color=th.warning, focused_border_color=th.success,
        color=th.text_main, bgcolor="#10ffffff" if th.is_dark else "#0a000000", border=ft.InputBorder.OUTLINE,
        text_size=24, text_align=ft.TextAlign.CENTER, border_radius=16,
    )

    strength_bar = ft.Container(width=0, height=4, bgcolor=th.border, border_radius=2, visible=False)
    strength_label = ft.Text("", size=11, color=th.text_dim, visible=False)
    strength_bar_bg = ft.Container(height=4, bgcolor="#10ffffff", border_radius=2, visible=False, content=strength_bar)

    rule_icons = {
        "len": ft.Text("○ En az 8 karakter", size=11, color=th.text_muted),
        "upper": ft.Text("○ Büyük harf (A-Z)", size=11, color=th.text_muted),
        "digit": ft.Text("○ Rakam (0-9)", size=11, color=th.text_muted),
        "special": ft.Text("○ Sembol", size=11, color=th.text_muted),
    }
    rules_row = ft.Row(list(rule_icons.values()), spacing=8, visible=False, wrap=True)

    def on_password_change(e):
        pw = password_field.value or ""
        if not is_register[0] or len(pw) == 0:
            strength_bar_bg.visible = False
            strength_label.visible = False
            rules_row.visible = False
            page.update()
            return
        score, label, color = _password_score(pw)
        strength_bar.width = max(10, score * 100)
        strength_bar.bgcolor = color
        strength_bar_bg.visible = True
        strength_label.value = label
        strength_label.color = color
        strength_label.visible = True
        rules_row.visible = True

        def _rule(ok, key, text):
            rule_icons[key].value = ("● " if ok else "○ ") + text
            rule_icons[key].color = th.success if ok else th.text_muted

        _rule(len(pw) >= 8, "len", "En az 8 karakter")
        _rule(bool(re.search(r"[A-Z]", pw)), "upper", "Büyük harf (A-Z)")
        _rule(bool(re.search(r"\d", pw)), "digit", "Rakam (0-9)")
        _rule(bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", pw)), "special", "Sembol")
        page.update()

    password_field.on_change = on_password_change

    error_box = ft.Container(
        content=ft.Row([ft.Icon(ft.icons.INFO_OUTLINE_ROUNDED, color=th.error, size=18), ft.Text("", color=th.error, size=13, expand=True, weight=ft.FontWeight.W_500)]),
        bgcolor="#1a" + th.error.replace("#", ""), padding=12, border_radius=12, visible=False,
        border=ft.border.all(1, "#33" + th.error.replace("#", ""))
    )
    loading_ring = ft.ProgressRing(color="#ffffff", visible=False, width=20, height=20, stroke_width=2)

    title_text = ft.Text("Tekrar Hoş Geldiniz", size=28, weight=ft.FontWeight.W_800, color=th.text_main, font_family="Inter")
    subtitle_text = ft.Text("Sentinel AI ile Araştırmaya Devam Edin", size=14, color=th.text_dim)

    action_btn = ft.ElevatedButton(
        content=ft.Row([ft.Text("Giriş Yap", size=16, weight=ft.FontWeight.BOLD, color="#ffffff"), loading_ring], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=th.accent, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        width=400, height=52,
    )
    
    toggle_btn = ft.TextButton(content=ft.Text("Hesap Oluştur", color=th.text_main, weight=ft.FontWeight.W_600), style=ft.ButtonStyle(overlay_color="#10ffffff"))
    forgot_btn = ft.TextButton(content=ft.Text("Şifremi Unuttum", color=th.text_main, weight=ft.FontWeight.W_600), style=ft.ButtonStyle(overlay_color="#10ffffff"), on_click=_open_forgot)
    
    links_row = ft.Row([forgot_btn, toggle_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def _handle_api_error(ex: Exception):
        import httpx, json as _json
        msg = "Bilinmeyen bir hata oluştu."
        
        # httpx.HTTPStatusError ise doğrudan response body'den detail çek
        if isinstance(ex, httpx.HTTPStatusError):
            try:
                body = ex.response.json()
                msg = body.get("detail", str(ex))
            except Exception:
                msg = ex.response.text or str(ex)
        else:
            raw = str(ex)
            # Client error '400 Bad Request' for url '...' şeklinde geliyor olabilir
            # httpx hatalarının içinde JSON gömülü olabiliyor
            if "Client error" in raw or "Server error" in raw:
                msg = "Sunucu işlemi reddetti. Bilgilerinizi kontrol edin."
            elif raw:
                msg = raw
        
        # Kullanıcı dostu Türkçe çeviriler
        friendly = {
            "E-posta veya şifre hatalı.": "❌ Girdiğiniz e-posta veya şifre hatalı!",
            "Bu e-posta zaten kayıtlı.": "⚠️ Bu e-posta adresi zaten kayıtlı. Giriş yapmayı deneyin.",
            "Geçersiz e-posta formatı.": "📧 Geçersiz bir e-posta adresi girdiniz.",
        }
        for key, val in friendly.items():
            if key.lower() in msg.lower():
                msg = val
                break
        
        # Şifre zayıf uyarıları
        if "şifre zayıf" in msg.lower() or "Şifre zayıf" in msg:
            msg = "🔒 " + msg.replace("Şifre zayıf: ", "Şifreniz yeterince güçlü değil:\n")
        
        # Hesap kilitli
        if "kilitlendi" in msg.lower():
            msg = "🔐 " + msg
        
        error_box.content.controls[1].value = msg
        error_box.visible = True
        page.update()

    # --- 2FA KURULUM YÖNETİMİ ---
    setup_2fa_ui = ft.Column(visible=False, spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    qr_image = ft.Image(visible=False, width=160, height=160, border_radius=16)
    secret_text = ft.Text("", size=12, color=th.text_dim, selectable=True, weight=ft.FontWeight.BOLD)
    setup_code_field = ft.TextField(hint_text="Kod", max_length=6, width=150, text_align=ft.TextAlign.CENTER, text_size=20, border_color=th.warning, focused_border_color=th.success, color=th.text_main, visible=False, bgcolor="#10ffffff", border_radius=12)
    setup_btn = ft.ElevatedButton(
        content=ft.Text("QR Kodu Oluştur", color="#000000", weight=ft.FontWeight.BOLD, size=15),
        bgcolor=th.warning, height=48, on_click=lambda e: _start_2fa_setup(),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
    )
    verify_setup_btn = ft.ElevatedButton(
        content=ft.Text("Doğrula ve Bitir", color="#ffffff", weight=ft.FontWeight.BOLD, size=15),
        bgcolor=th.success, height=48, visible=False, on_click=lambda e: _verify_2fa_setup(),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
    )
    skip_btn = ft.TextButton("Şimdilik Atlamak İstiyorum", style=ft.ButtonStyle(color=th.text_dim), on_click=lambda e: _finish_login())
    
    current_login_data = [{}]

    def _start_2fa_setup():
        try:
            data = api_client.setup_2fa(pending_email[0])
            qr_image.src_base64 = data.get("qr_code_base64")
            secret_text.value = f"Manuel Girdi Kodu: {data.get('secret')}"
            qr_image.visible = True
            secret_text.visible = True
            setup_code_field.visible = True
            verify_setup_btn.visible = True
            setup_btn.visible = False
            error_box.visible = False
        except Exception as ex: _handle_api_error(ex)
        page.update()

    def _verify_2fa_setup():
        code = setup_code_field.value.strip()
        if len(code) != 6:
            _handle_api_error(Exception("Lütfen tam 6 haneli kodu giriniz."))
            page.update(); return
        try:
            api_client.verify_2fa_setup(pending_email[0], code)
            api_client.user_info["totp_enabled"] = True
            _finish_login()
        except Exception as ex: _handle_api_error(Exception("Girdiğiniz kod hatalı. Tekrar deneyin."))
        page.update()

    def _switch_to_2fa_offer(login_data):
        current_login_data[0] = login_data
        
        email_field.visible = False
        password_field.visible = False
        username_field.visible = False
        groq_key_field.visible = False
        gemini_key_field.visible = False
        deepseek_key_field.visible = False
        links_row.visible = False
        action_btn.visible = False
        strength_bar_bg.visible = False
        rules_row.visible = False
        
        title_text.value = "Kalkan Aktifleştirilsin mi?"
        subtitle_text.value = "Hesabınızı 2 Aşamalı Doğrulama (2FA) ile korumanız şiddetle tavsiye edilir."
        setup_2fa_ui.visible = True
        page.update()

    def _finish_login(): on_login_success(current_login_data[0])

    def _set_loading(state: bool):
        loading_ring.visible = state
        if state: action_btn.content.controls[0].value = "Bağlanıyor..."
        else: action_btn.content.controls[0].value = "Kayıt Ol" if is_register[0] else "Giriş Yap"
        if pending_2fa[0]: action_btn.content.controls[0].value = "Doğrula"
        action_btn.disabled  = state
        page.update()

    def handle_action(e):
        error_box.visible = False
        if pending_2fa[0]:
            code = totp_field.value.strip()
            if len(code) != 6 or not code.isdigit():
                _handle_api_error(Exception("Lütfen 6 haneli kod girin.")); return
            _set_loading(True)
            try:
                data = api_client.verify_2fa_login(email=pending_email[0], code=code)
                api_client.user_info = data.get("user", {"email": pending_email[0]})
                on_login_success(data)
            except Exception as ex: _handle_api_error(Exception("Kod hatalı."))
            finally: _set_loading(False)
            return

        email, password = email_field.value.strip(), password_field.value.strip()
        if not email or not password:
            _handle_api_error(Exception("E-Posta ve Şifre boş bırakılamaz.")); return

        _set_loading(True)
        try:
            if is_register[0]:
                username = username_field.value.strip() or email.split("@")[0]
                data = api_client.register(
                    email=email, password=password, username=username,
                    groq_key=groq_key_field.value.strip(),
                    gemini_key=gemini_key_field.value.strip(),
                    deepseek_key=deepseek_key_field.value.strip()
                )
                api_client.user_info = {"email": email, **data}
                login_data = api_client.login(email=email, password=password)
                if not login_data.get("requires_2fa"):
                    api_client.user_info = login_data.get("user", {"email": email})
                    pending_email[0] = email
                    _switch_to_2fa_offer(login_data)
            else:
                data = api_client.login(email=email, password=password)
                pending_email[0] = email
                if data.get("requires_2fa"):
                    pending_2fa[0]   = True
                    title_text.value = "2FA Doğrulama"
                    subtitle_text.value = "Authenticator kodunuzu girin."
                    email_field.visible = password_field.visible = username_field.visible = False
                    groq_key_field.visible = gemini_key_field.visible = deepseek_key_field.visible = False
                    totp_field.visible = True
                    action_btn.content.controls[0].value = "Doğrula"
                    links_row.visible = False
                    page.update()
                else:
                    api_client.user_info = data.get("user", {"email": email})
                    if not api_client.user_info.get("totp_enabled"): _switch_to_2fa_offer(data)
                    else: on_login_success(data)
        except Exception as ex: _handle_api_error(ex)
        finally: _set_loading(False)

    def toggle_mode(e):
        is_register[0] = not is_register[0]
        username_field.visible = is_register[0]
        groq_key_field.visible = is_register[0]
        gemini_key_field.visible = is_register[0]
        deepseek_key_field.visible = is_register[0]
        forgot_btn.visible = not is_register[0]
        title_text.value = "Hesap Oluştur" if is_register[0] else "Tekrar Hoş Geldiniz"
        subtitle_text.value = "Yeni bir hesap oluşturarak güçlü asistanı kullanın" if is_register[0] else "Sentinel AI ile Araştırmaya Devam Edin"
        action_btn.content.controls[0].value = "Kayıt Ol" if is_register[0] else "Giriş Yap"
        toggle_btn.content.value  = "Zaten hesabınız var mı?" if is_register[0] else "Hesabınız yok mu? Kayıt Olun"
        error_box.visible = False
        if is_register[0] and password_field.value: on_password_change(None)
        else: strength_bar_bg.visible = strength_label.visible = rules_row.visible = False
        page.update()

    setup_2fa_ui.controls = [qr_image, secret_text, setup_code_field, ft.Row([setup_btn, verify_setup_btn], alignment=ft.MainAxisAlignment.CENTER), skip_btn]
    action_btn.on_click = handle_action
    toggle_btn.on_click = toggle_mode

    # -- MACOS / WINDOWS 11 GLASSMORPHISM KART YAPISI --
    glass_card = ft.Container(
        width=480, padding=ft.padding.symmetric(horizontal=48, vertical=48),
        bgcolor="#14141d" if th.is_dark else "#f0f0f5",
        border_radius=24,
        border=ft.border.all(1, "#2a2a35" if th.is_dark else "#e0e0e0"),
        shadow=ft.BoxShadow(blur_radius=100, color="#1e90ff44" if th.is_dark else "#44444422", spread_radius=-10, offset=ft.Offset(0, 30)),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16,
            controls=[
                ft.Container(
                    width=64, height=64, border_radius=32, bgcolor="#20ffffff" if th.is_dark else "#10000000",
                    border=ft.border.all(1, "#30ffffff"), content=ft.Icon(ft.icons.FINGERPRINT, size=32, color=th.accent),
                    alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=20, color=th.accent + "aa")
                ),
                title_text, subtitle_text,
                ft.Container(height=8),
                error_box,
                username_field, email_field, password_field,
                groq_key_field, gemini_key_field, deepseek_key_field,
                ft.Row([strength_bar_bg, strength_label], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                rules_row, totp_field, setup_2fa_ui,
                ft.Container(height=8),
                action_btn, links_row,
            ]
        ),
    )

    bg_stack = ft.Stack(
        expand=True,
        controls=[
            ft.Container(expand=True, bgcolor=th.bg),
            # Arka plandaki dev yansıma (Glow effect)
            ft.Container(
                width=600, height=600, border_radius=300, bgcolor=th.accent, opacity=0.15 if th.is_dark else 0.05,
                left=-200, top=-200, blur=ft.Blur(sigma_x=100, sigma_y=100)
            ),
            ft.Container(
                width=800, height=800, border_radius=400, bgcolor=th.warning, opacity=0.1 if th.is_dark else 0.05,
                right=-300, bottom=-300, blur=ft.Blur(sigma_x=120, sigma_y=120)
            ),
            # Kartı tam ortaya koyma
            ft.Container(expand=True, alignment=ft.alignment.center, content=glass_card),
            forgot_overlay
        ]
    )

    return bg_stack
