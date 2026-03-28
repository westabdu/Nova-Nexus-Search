"""
Admin View - Yönetici Paneli
Tüm kullanıcıların kotalarını ve özelliklerini listeleyen ekran.
"""
import flet as ft
from frontend.utils.theme import current_theme as th
from loguru import logger

def build_admin_view(page: ft.Page, api_client, on_close) -> ft.Container:
    msg_text = ft.Text("", size=12)
    users_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

    def show_msg(msg: str, color: str):
        msg_text.value = msg
        msg_text.color = color
        page.update()

    def load_users():
        users_list.controls.clear()
        try:
            users = api_client.get_all_users()
            for u in users:
                # Kullanıcı Kartı
                uid = u["id"]
                email = u["email"]
                quota = u["quota_remaining"]
                is_active = u["is_active"]
                is_admin = u["is_admin"]

                quota_field = ft.TextField(
                    value=str(quota), width=60, height=30, text_size=12,
                    content_padding=4, keyboard_type=ft.KeyboardType.NUMBER,
                    bgcolor=th.surface_variant, color=th.text_main, border_color=th.border
                )

                def on_quota_save(e, user_id=uid, q_field=quota_field):
                    try:
                        new_q = int(q_field.value)
                        api_client.update_user_quota(user_id, new_q)
                        show_msg(f"Kota güncellendi (Kullanıcı ID: {user_id})", th.success)
                    except Exception as ex:
                        show_msg(f"Kota güncelleme hatası: {ex}", th.error)

                def on_toggle_status(e, user_id=uid):
                    try:
                        res = api_client.toggle_user_status(user_id)
                        show_msg(res["message"], th.success if res["is_active"] else th.warning)
                        load_users()
                    except Exception as ex:
                        show_msg(f"Durum güncelleme hatası: {ex}", th.error)

                status_color = th.success if is_active else th.error
                status_text = "Aktif" if is_active else "Pasif"
                admin_badge = "🛡️ Admin" if is_admin else "👤 Kullanıcı"

                card = ft.Container(
                    padding=10, bgcolor=th.surface_variant, border_radius=8,
                    border=ft.border.all(1, th.border),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(email, weight=ft.FontWeight.W_600, color=th.text_main, size=13),
                            ft.Text(admin_badge, size=11, color=th.text_dim),
                        ], expand=True),
                        ft.Container(
                            ft.Text(status_text, color=status_color, size=11, weight=ft.FontWeight.W_600),
                            padding=4, bgcolor=th.success_bg if is_active else th.error_bg, border_radius=6
                        ),
                        ft.Row([
                            ft.Text("Kota:", size=11, color=th.text_dim),
                            quota_field,
                            ft.IconButton(icon=ft.icons.SAVE, icon_size=16, icon_color=th.accent, on_click=on_quota_save),
                        ], spacing=4),
                        ft.IconButton(
                            icon=ft.icons.BLOCK if is_active else ft.icons.CHECK_CIRCLE,
                            icon_size=16,
                            icon_color=th.error if is_active else th.success,
                            tooltip="Durumu Değiştir",
                            on_click=on_toggle_status
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
                users_list.controls.append(card)
        except Exception as ex:
            show_msg(f"Kullanıcılar yüklenemedi: {ex}", th.error)
            logger.error(f"Admin API error: {ex}")
        page.update()

    load_users()

    return ft.Container(
        expand=True, padding=24, bgcolor=th.bg, border_radius=12,
        border=ft.border.all(1, th.border),
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, color=th.accent, size=24),
                ft.Text("Yönetim Paneli", size=18, weight=ft.FontWeight.BOLD, color=th.text_main),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.icons.CLOSE, icon_color=th.text_muted, on_click=lambda e: on_close())
            ]),
            ft.Divider(color=th.border),
            msg_text,
            ft.Container(
                content=users_list,
                expand=True,
            )
        ], spacing=12)
    )
