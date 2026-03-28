"""
Nova Nexus Search - Ana Flet Uygulaması (Flet 0.24.x uyumlu)
"""
import sys
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import flet as ft
from frontend.views.auth_view import build_auth_view
from frontend.views.dashboard_view import build_dashboard_view
from frontend.utils.api_client import APIClient

api_client = APIClient()
current_lang = ["tr"]


def main(page: ft.Page):
    page.title = "Nova Nexus Search"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#050a14"
    page.padding = 0
    page.window.width = 1400
    page.window.height = 860
    page.window.min_width = 960
    page.window.min_height = 640
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    }

    def show_auth():
        page.controls.clear()
        auth = build_auth_view(
            page=page,
            api_client=api_client,
            on_login_success=lambda data: show_dashboard(),
            current_lang=current_lang[0],
        )
        page.controls.append(ft.Container(content=auth, expand=True))
        page.update()

    def show_dashboard():
        page.controls.clear()
        dashboard = build_dashboard_view(
            page=page,
            api_client=api_client,
            current_lang_ref=current_lang,
            on_logout=lambda: (api_client.logout(), show_auth()),
        )
        page.controls.append(ft.Container(content=dashboard, expand=True))
        page.update()

    show_auth()


if __name__ == "__main__":
    if os.environ.get("FLET_WEB_MODE") == "1":
        # Docker ortamında web sunucusu olarak kalkar
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8550)
    else:
        ft.app(target=main)
