"""
Dashboard View - macOS x Windows 11 Premium Komuta Merkezi
Nova Nexus v3.0 — Araştırma + Arşiv + Karşılaştırma (Tam Aktif)
"""
import flet as ft
import asyncio
import websockets
import json
import threading
import subprocess
from frontend.utils.i18n import t, LANGUAGE_NAMES
from frontend.views.profile_panel import build_profile_panel
from frontend.utils.theme import current_theme as th
from loguru import logger

WS_BASE = "http://127.0.0.1:8000".replace("http", "ws")

def build_dashboard_view(page: ft.Page, api_client, current_lang_ref: list, on_logout):
    lang = current_lang_ref[0]
    saved_files_holder = [{}]

    def show_toast(msg: str, color: str = None):
        if color is None: color = th.success
        page.open(ft.SnackBar(content=ft.Text(msg, color="#ffffff"), bgcolor=color, duration=3000))
        page.update()

    profile_sidebar = build_profile_panel(page, api_client, lang)

    # ═══════════════════════════════════════════════════════════════
    #  TAB 1: ARAŞTIRMA
    # ═══════════════════════════════════════════════════════════════
    log_col = ft.Column(spacing=4, expand=True, scroll=ft.ScrollMode.ALWAYS, auto_scroll=True)

    def add_log(msg: str):
        color_map = {"🔍": th.accent, "✅": th.success, "❌": th.error, "⛔": th.error, "⚠️": th.warning,
                     "🎉": th.accent, "🔌": th.accent, "⏱️": th.text_dim, "🧠": th.warning,
                     "🌐": th.accent, "📥": th.success, "⚡": th.warning, "✨": th.success,
                     "📝": th.text_main, "🔎": th.accent, "✔️": th.success, "📋": th.accent}
        c = th.text_main
        for emoji, col in color_map.items():
            if msg.startswith(emoji): c = col; break
        log_col.controls.append(ft.Text(f" {msg}", size=12, color=c, selectable=True, font_family="Consolas"))
        page.update()

    dd_style = dict(
        border_color="transparent", color=th.text_main,
        bgcolor="#10ffffff" if th.is_dark else "#0a000000",
        border_radius=12, text_size=13
    )

    query_field = ft.TextField(
        hint_text="Derin araştırma yapmak istediğiniz konuyu yazın...",
        prefix_icon=ft.icons.SEARCH_ROUNDED, expand=True,
        border_color="transparent", focused_border_color=th.accent,
        color=th.text_main, bgcolor="#10ffffff" if th.is_dark else "#0a000000",
        border_radius=16, text_size=18, height=64,
        content_padding=ft.padding.only(left=20, top=20, bottom=20),
        on_submit=lambda e: page.run_task(start_search),
    )

    depth_dd = ft.Dropdown(label="Derinlik", value="deep", width=110, **dd_style, options=[
        ft.dropdown.Option(key="medium", text="Orta"), ft.dropdown.Option(key="deep", text="Derin"), ft.dropdown.Option(key="ultra", text="Ultra"),
    ])
    time_dd = ft.Dropdown(label="Zaman", value="all", width=110, **dd_style, options=[
        ft.dropdown.Option(key="all", text="Tümü"), ft.dropdown.Option(key="1y", text="Son 1 Yıl"), ft.dropdown.Option(key="1m", text="Son 1 Ay"),
    ])
    domain_dd = ft.Dropdown(label="Domain", value="all", width=110, **dd_style, options=[
        ft.dropdown.Option(key="all", text="Genel"), ft.dropdown.Option(key="edu", text="Akademik (.edu)"), ft.dropdown.Option(key="gov", text="Resmi (.gov)"),
    ])
    max_src_dd = ft.Dropdown(label="Kaynak", value="0", width=110, **dd_style, options=[
        ft.dropdown.Option(key="0", text="Otomatik"), ft.dropdown.Option(key="10", text="10 URL"), ft.dropdown.Option(key="20", text="20 URL"),
    ])
    out_lang_dd = ft.Dropdown(label="Dil", value=lang, width=120, **dd_style, options=[
        ft.dropdown.Option(key=k, text=v) for k, v in LANGUAGE_NAMES.items()
    ])

    _fmt_state = {"md": True, "html": True, "json": False, "pdf": False}
    def _make_fmt_btn(key, label):
        def toggle(e):
            _fmt_state[key] = not _fmt_state[key]
            e.control.bgcolor = th.accent if _fmt_state[key] else "#10ffffff"
            e.control.content.color = "#ffffff" if _fmt_state[key] else th.text_muted
            page.update()
        return ft.Container(
            content=ft.Text(label, size=11, color="#ffffff" if _fmt_state[key] else th.text_muted, weight=ft.FontWeight.W_600),
            bgcolor=th.accent if _fmt_state[key] else "#10ffffff",
            border_radius=8, padding=ft.padding.symmetric(vertical=6, horizontal=12), on_click=toggle, ink=True
        )

    search_btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.icons.ROCKET_LAUNCH_ROUNDED, color="#ffffff"), ft.Text("Araştır", color="#ffffff", weight=ft.FontWeight.BOLD)], spacing=8),
        bgcolor=th.accent, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=lambda e: page.run_task(start_search),
    )

    synthesis_md = ft.Markdown(value="", selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark" if th.is_dark else "atom-one-light")
    src_list = ft.ListView(spacing=12, height=450)
    val_score = ft.Text("", size=48, weight=ft.FontWeight.W_900, color=th.accent)
    val_status = ft.Text("", size=16, color=th.text_dim, weight=ft.FontWeight.W_800)
    val_reason = ft.Text("", size=14, color=th.text_main, italic=True)

    validation_col = ft.Container(
        padding=24, bgcolor="#10ffffff" if th.is_dark else "#f4f4f8", border_radius=20, 
        border=ft.border.all(1, "#30ffffff" if th.is_dark else "#e0e0e8"),
        shadow=ft.BoxShadow(blur_radius=30, color=th.accent + "11", spread_radius=5, offset=ft.Offset(0, 5)),
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.SHIELD_ROUNDED, color=th.success, size=24), ft.Text("Güvenilirlik Analizi", size=16, weight=ft.FontWeight.W_800, color=th.text_main)]),
            ft.Divider(color="#20ffffff" if th.is_dark else "#d0d0d8", height=1),
            ft.Row([val_score, ft.Column([ft.Text("DOĞRULUK SKORU", size=11, weight=ft.FontWeight.BOLD, color=th.text_muted), val_status], spacing=0)], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=4),
            val_reason,
        ], spacing=12)
    )

    download_row = ft.Row(visible=False, wrap=True)
    def bind_download_buttons(files_dict):
        download_row.controls = [ft.Text("Dışa Aktar:", size=13, weight=ft.FontWeight.W_600, color=th.text_main)]
        for fmt, link in files_dict.items():
            btn = ft.Container(
                content=ft.Row([ft.Icon(ft.icons.DOWNLOAD_ROUNDED, size=14, color="#fff"), ft.Text(fmt.upper(), size=12, color="#fff", weight=ft.FontWeight.W_700)]),
                padding=ft.padding.symmetric(horizontal=12, vertical=8), border_radius=8,
                bgcolor=th.accent, on_click=lambda e, u=link: page.launch_url(u), ink=True
            )
            download_row.controls.append(btn)
        if files_dict: download_row.visible = True
        page.update()

    report_content_container = ft.Container(
        padding=32, bgcolor="#0a000000" if th.is_dark else "#ffffff", border_radius=20,
        border=ft.border.all(1, "#20ffffff" if th.is_dark else "#e0e0e8"),
        content=synthesis_md
    )

    report_panel = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.ADAPTIVE, controls=[
        ft.Row([
            ft.Row([ft.Icon(ft.icons.ARTICLE_ROUNDED, size=28, color=th.accent), ft.Text("Derin Analiz Raporu", size=24, weight=ft.FontWeight.W_900, color=th.text_main)], spacing=12),
            ft.Container(expand=True),
            download_row
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=16),
        ft.Row([
            ft.Container(expand=5, content=report_content_container),
            ft.Container(width=1, bgcolor=th.border),
            ft.Container(expand=2, padding=16, content=ft.Column([
                validation_col,
                ft.Container(height=24),
                ft.Row([ft.Icon(ft.icons.LIBRARY_BOOKS_ROUNDED, size=20, color=th.text_dim), ft.Text("Yararlanılan Kaynaklar", size=16, weight=ft.FontWeight.W_800, color=th.text_main)]),
                ft.Container(height=8),
                src_list,
            ], scroll=ft.ScrollMode.ADAPTIVE))
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
    ])

    log_panel = ft.Container(
        visible=False, height=200, bgcolor="#08000000", border_radius=12, padding=12,
        border=ft.border.all(1, "#15ffffff"),
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.TERMINAL_ROUNDED, size=16, color=th.text_dim), ft.Text("Sentinel Logs", size=13, weight=ft.FontWeight.W_700, color=th.text_dim)]),
            log_col
        ])
    )

    def show_report(data):
        report_panel.visible = True
        synthesis_md.value = data.get("synthesis", "Sentez verisi bulunamadı.")
        src_list.controls.clear()
        for doc in data.get("documents", []):
            src_list.controls.append(ft.Container(
                padding=10, bgcolor="#10ffffff", border_radius=8, border=ft.border.all(1, "#20ffffff"),
                content=ft.Column([
                    ft.Text(doc.get("title",""), size=13, weight=ft.FontWeight.W_600, color=th.text_main, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(doc.get("url",""), size=11, color=th.accent, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"Skor: {doc.get('relevance_score','?')}/10", size=10, color=th.success)
                ], spacing=2),
                on_click=lambda e, u=doc.get("url",""): page.launch_url(u), ink=True
            ))
        val = data.get("validation", {})
        sc = val.get("reliability_score", 0)
        val_score.value = f"{sc}/10"
        val_score.color = th.success if sc >= 7 else (th.warning if sc >= 4 else th.error)
        val_status.value = "Yüksek Güvenilirlik" if sc >= 7 else ("Orta" if sc >= 4 else "Düşük")
        val_reason.value = str(val.get("verdict", ""))
        page.update()

    async def start_search():
        q = query_field.value.strip()
        if not q: return show_toast("Lütfen araştırılacak konuyu girin.", th.error)
        log_col.controls.clear()
        log_panel.visible = True
        report_panel.visible = False
        synthesis_md.value = ""
        download_row.visible = False
        page.update()

        add_log("🔌 Bağlantı kuruluyor...")
        fmts = [f for f, st in _fmt_state.items() if st]
        user_email = api_client._email()
        try:
            # Önce session_id al
            session_data = api_client.start_research_session()
            sid = session_data.get("session_id", "unknown")
            add_log(f"🔍 Oturum oluşturuldu: {sid[:8]}...")

            ws = await websockets.connect(
                f"{WS_BASE}/api/research/ws/research/{sid}",
                ping_interval=30,
                ping_timeout=120,
                close_timeout=300,
            )
            req = {
                "query": q, "depth": depth_dd.value, "time_filter": time_dd.value,
                "domain_filter": domain_dd.value, "max_sources": int(max_src_dd.value),
                "language": out_lang_dd.value, "formats": fmts, "user_email": user_email,
                "groq_api_key": api_client.user_info.get("groq_api_key", "") if api_client.user_info else "",
                "gemini_api_key": api_client.user_info.get("gemini_api_key", "") if api_client.user_info else "",
                "deepseek_api_key": api_client.user_info.get("deepseek_api_key", "") if api_client.user_info else "",
            }
            await ws.send(json.dumps(req))
            while True:
                msg = await ws.recv()
                pkt = json.loads(msg)
                tt = pkt.get("type")
                if tt == "progress": add_log(pkt.get("message", ""))
                elif tt == "result":
                    res = pkt.get("data", {})
                    files = pkt.get("files", {})
                    if "error" in res:
                        add_log(f"⛔ Hata: {res['error']}")
                    else:
                        add_log("🎉 Araştırma tamamlandı!")
                        show_report(res)
                        bind_download_buttons(files)
                    break
                elif tt == "error":
                    add_log(f"❌ Sunucu Hatası: {pkt.get('message')}"); break
            await ws.close()
        except Exception as ex:
            if hasattr(ex, 'code') and getattr(ex, 'code', None) == 1000:
                pass
            else:
                add_log(f"❌ Bağlantı hatası: {ex}")
                show_toast(f"Bağlantı hatası: {ex}", th.error)

    research_view = ft.Column(expand=True, spacing=16, controls=[
        # Başlık
        ft.Text("Araştırma Merkezi", size=22, weight=ft.FontWeight.W_800, color=th.text_main),
        # Arama kutusu ve filtreler
        ft.Container(
            padding=32, bgcolor="#10ffffff" if th.is_dark else "#fcfcfd", border_radius=20,
            border=ft.border.all(1, "#20ffffff" if th.is_dark else "#e0e0e8"),
            shadow=ft.BoxShadow(blur_radius=40, color=th.accent + "22", spread_radius=-5, offset=ft.Offset(0, 10)),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.TRAVEL_EXPLORE_ROUNDED, size=28, color=th.accent),
                    ft.Text("Nova Derin Araştırma Motoru", size=20, weight=ft.FontWeight.W_800, color=th.text_main),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Sadece ne aradığınızı söyleyin. Sentinel AI geri kalanı halletsin.", size=13, color=th.text_dim, text_align=ft.TextAlign.CENTER),
                ft.Container(height=12),
                ft.Row([query_field, search_btn], spacing=12),
                ft.Container(height=8),
                ft.Row([depth_dd, time_dd, domain_dd, max_src_dd, out_lang_dd], spacing=8, wrap=True),
                ft.Container(height=4),
                ft.Row([ft.Text("Formatlar:", size=12, color=th.text_dim), _make_fmt_btn("md","MD"), _make_fmt_btn("html","HTML"), _make_fmt_btn("json","JSON"), _make_fmt_btn("pdf","PDF")], spacing=8),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),
        # Log paneli (araştırma başlayınca görünür)
        log_panel,
        # Rapor paneli (araştırma bitince görünür)
        report_panel,
    ])

    # ═══════════════════════════════════════════════════════════════
    #  TAB 2: VERİ ARŞİVİ (Geçmiş Araştırmalar)
    # ═══════════════════════════════════════════════════════════════
    history_list_col = ft.Column(spacing=8, expand=True, scroll=ft.ScrollMode.ADAPTIVE)
    history_detail_md = ft.Markdown(value="", selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark" if th.is_dark else "atom-one-light")
    history_detail_panel = ft.Container(visible=False, expand=True, padding=24, bgcolor="#08ffffff" if th.is_dark else "#fafafa", border_radius=16, content=ft.Column([
        ft.TextButton("← Listeye Dön", on_click=lambda e: _close_detail(), style=ft.ButtonStyle(color=th.accent)),
        history_detail_md
    ], scroll=ft.ScrollMode.ADAPTIVE))
    history_list_panel = ft.Container(expand=True, content=history_list_col)

    def _close_detail():
        history_detail_panel.visible = False
        history_list_panel.visible = True
        page.update()

    def _open_detail(hid):
        try:
            detail = api_client.get_research_detail(hid)
            history_detail_md.value = detail.get("synthesis", detail.get("content", "İçerik bulunamadı."))
            history_detail_panel.visible = True
            history_list_panel.visible = False
        except Exception as ex:
            show_toast(f"Detay yüklenemedi: {ex}", th.error)
        page.update()

    def _toggle_fav(hid):
        try:
            api_client.toggle_history_favorite(hid)
            _load_history()
        except: pass

    def _delete_history(hid):
        try:
            api_client.delete_history(hid)
            _load_history()
            show_toast("Araştırma silindi.", th.warning)
        except Exception as ex:
            show_toast(f"Silinemedi: {ex}", th.error)

    def _load_history():
        history_list_col.controls.clear()
        try:
            items = api_client.get_research_history()
            if not items:
                history_list_col.controls.append(ft.Container(
                    alignment=ft.alignment.center, expand=True,
                    content=ft.Column([
                        ft.Icon(ft.icons.INBOX_OUTLINED, size=60, color=th.border),
                        ft.Text("Henüz araştırma yapılmamış.", size=16, color=th.text_muted),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
                ))
            else:
                for item in items:
                    hid = item.get("id")
                    is_fav = item.get("is_favorite", False)
                    dt = str(item.get("created_at", "")).replace("T", " ")[:16]
                    tags = item.get("tags", "") or ""
                    score = item.get("reliability_score", 0)
                    score_color = th.success if score >= 7 else (th.warning if score >= 4 else th.error)

                    card = ft.Container(
                        padding=16, bgcolor="#10ffffff" if th.is_dark else "#f8f8fc", border_radius=12,
                        border=ft.border.all(1, "#20ffffff" if th.is_dark else "#e8e8ee"),
                        ink=True, on_click=lambda e, _id=hid: _open_detail(_id),
                        content=ft.Row([
                            ft.Container(
                                width=48, height=48, border_radius=12,
                                bgcolor=score_color + "22",
                                content=ft.Text(f"{score}", size=18, weight=ft.FontWeight.W_900, color=score_color, text_align=ft.TextAlign.CENTER),
                                alignment=ft.alignment.center
                            ),
                            ft.Column([
                                ft.Text(item.get("query", "?"), size=15, weight=ft.FontWeight.W_700, color=th.text_main, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row([
                                    ft.Text(f"{item.get('depth','?')} • {item.get('source_count',0)} kaynak • {dt}", size=11, color=th.text_dim),
                                    *([ft.Container(
                                        bgcolor=th.accent+"22", border_radius=4, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                        content=ft.Text(tags, size=10, color=th.accent)
                                    )] if tags else []),
                                ], spacing=8, wrap=True),
                            ], expand=True, spacing=2),
                            ft.IconButton(
                                icon=ft.icons.STAR_ROUNDED if is_fav else ft.icons.STAR_OUTLINE_ROUNDED,
                                icon_color=th.warning if is_fav else th.text_muted, icon_size=20,
                                on_click=lambda e, _id=hid: _toggle_fav(_id), tooltip="Favori"
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE_ROUNDED, icon_color=th.error, icon_size=18,
                                on_click=lambda e, _id=hid: _delete_history(_id), tooltip="Sil"
                            ),
                        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                    history_list_col.controls.append(card)
        except Exception as ex:
            history_list_col.controls.append(ft.Text(f"Yüklenemedi: {ex}", color=th.error))
        page.update()

    history_view = ft.Column(expand=True, spacing=16, controls=[
        ft.Row([
            ft.Text("Veri Arşivi", size=22, weight=ft.FontWeight.W_800, color=th.text_main),
            ft.Container(expand=True),
            ft.ElevatedButton(
                content=ft.Row([ft.Icon(ft.icons.REFRESH_ROUNDED, color="#ffffff", size=18), ft.Text("Yenile", color="#ffffff", weight=ft.FontWeight.BOLD)], spacing=6),
                bgcolor=th.accent, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=lambda e: _load_history()),
        ]),
        ft.Text("Tüm geçmiş araştırmalarınız burada. Detay görmek için kartlara tıklayın.", size=13, color=th.text_dim),
        history_list_panel,
        history_detail_panel,
    ])

    # ═══════════════════════════════════════════════════════════════
    #  TAB 3: KARŞILAŞTIRMA
    # ═══════════════════════════════════════════════════════════════
    compare_items = [None, None]  # [left_id, right_id]
    compare_dd_left = ft.Dropdown(label="Sol Rapor", width=350, **dd_style, on_change=lambda e: _update_compare())
    compare_dd_right = ft.Dropdown(label="Sağ Rapor", width=350, **dd_style, on_change=lambda e: _update_compare())
    compare_left_md = ft.Markdown(value="", selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark" if th.is_dark else "atom-one-light")
    compare_right_md = ft.Markdown(value="", selectable=True, extension_set="gitHubWeb", code_theme="atom-one-dark" if th.is_dark else "atom-one-light")

    def _load_compare_options():
        try:
            items = api_client.get_research_history()
            opts = [ft.dropdown.Option(key=str(it["id"]), text=f"{it['query'][:50]} ({str(it.get('created_at',''))[:10]})") for it in items]
            compare_dd_left.options = opts
            compare_dd_right.options = list(opts)  # copy
        except: pass
        page.update()

    def _update_compare():
        lid = compare_dd_left.value
        rid = compare_dd_right.value
        if lid:
            try:
                d = api_client.get_research_detail(int(lid))
                compare_left_md.value = d.get("synthesis", d.get("content", "İçerik yok."))
            except: compare_left_md.value = "Yüklenemedi."
        if rid:
            try:
                d = api_client.get_research_detail(int(rid))
                compare_right_md.value = d.get("synthesis", d.get("content", "İçerik yok."))
            except: compare_right_md.value = "Yüklenemedi."
        page.update()

    compare_view = ft.Column(expand=True, spacing=16, controls=[
        ft.Text("Kapsamlı Karşılaştırma", size=22, weight=ft.FontWeight.W_800, color=th.text_main),
        ft.Text("İki araştırma raporunu yan yana görüntüleyerek derinlemesine analiz yapın.", size=13, color=th.text_dim),
        ft.Row([compare_dd_left, compare_dd_right,
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.icons.REFRESH_ROUNDED, color="#ffffff", size=18), ft.Text("Yenile", color="#ffffff", weight=ft.FontWeight.BOLD)], spacing=6),
                    bgcolor=th.accent, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: _load_compare_options()),
        ], spacing=16, wrap=True),
        ft.Row([
            ft.Container(expand=1, padding=20, bgcolor="#08ffffff" if th.is_dark else "#f8f8fc", border_radius=16,
                         border=ft.border.all(1, "#20ffffff" if th.is_dark else "#e0e0e8"),
                         content=ft.Column([ft.Text("SOL RAPOR", size=12, weight=ft.FontWeight.W_700, color=th.accent), compare_left_md], scroll=ft.ScrollMode.ADAPTIVE)),
            ft.Container(width=2, bgcolor=th.border),
            ft.Container(expand=1, padding=20, bgcolor="#08ffffff" if th.is_dark else "#f8f8fc", border_radius=16,
                         border=ft.border.all(1, "#20ffffff" if th.is_dark else "#e0e0e8"),
                         content=ft.Column([ft.Text("SAĞ RAPOR", size=12, weight=ft.FontWeight.W_700, color=th.warning), compare_right_md], scroll=ft.ScrollMode.ADAPTIVE)),
        ], expand=True, spacing=8)
    ])

    # ═══════════════════════════════════════════════════════════════
    #  NAVIGATION RAIL + LAYOUT
    # ═══════════════════════════════════════════════════════════════
    views = [research_view, history_view, compare_view]
    research_view.visible = True
    history_view.visible = False
    compare_view.visible = False
    content_area = ft.Container(expand=True, content=ft.Stack(views, expand=True), padding=20)

    def _switch_tab(idx):
        for i, view in enumerate(views):
            view.visible = (i == idx)
        if idx == 1: _load_history()
        if idx == 2: _load_compare_options()
        page.update()

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL,
        min_width=80, min_extended_width=200, bgcolor="transparent",
        expand=True,
        destinations=[
            ft.NavigationRailDestination(icon=ft.icons.SCIENCE_OUTLINED, selected_icon=ft.icons.SCIENCE_ROUNDED, label="Araştırma"),
            ft.NavigationRailDestination(icon=ft.icons.HISTORY_OUTLINED, selected_icon=ft.icons.HISTORY_ROUNDED, label="Veri Arşivi"),
            ft.NavigationRailDestination(icon=ft.icons.COMPARE_ARROWS_OUTLINED, selected_icon=ft.icons.COMPARE_ARROWS_ROUNDED, label="Karşılaştırma"),
        ],
        on_change=lambda e: _switch_tab(e.control.selected_index)
    )

    # Profil Overlay
    profile_overlay = ft.Container(
        visible=False, width=340,
        padding=ft.padding.only(left=96, top=40),
        content=profile_sidebar
    )
    def toggle_profile(e):
        profile_overlay.visible = not profile_overlay.visible
        page.update()

    info = api_client.user_info or {}
    username = info.get("username", info.get("email", "NN").split("@")[0])
    initials = (username[:2] if username else "NN").upper()
    profile_btn = ft.Container(
        width=44, height=44, border_radius=22,
        bgcolor=th.surface_variant, border=ft.border.all(2, th.accent),
        content=ft.Text(initials, size=14, weight=ft.FontWeight.BOLD, color=th.accent, text_align=ft.TextAlign.CENTER),
        alignment=ft.alignment.center, on_click=toggle_profile, ink=True, tooltip="Profil & Ayarlar",
    )

    # Mica Glow + Ana Layout
    return ft.Stack(expand=True, controls=[
        ft.Container(expand=True, bgcolor=th.bg),
        ft.Container(width=700, height=700, border_radius=350, bgcolor=th.accent, opacity=0.06,
                     left=-200, bottom=-200, blur=ft.Blur(sigma_x=120, sigma_y=120)),
        ft.Row([
            ft.Container(
                width=88, bgcolor="#0d0d14" if th.is_dark else "#f4f4f7",
                border=ft.border.only(right=ft.border.BorderSide(1, "#22222e" if th.is_dark else "#e0e0e8")),
                padding=ft.padding.symmetric(vertical=12),
                content=ft.Column([
                    ft.Container(content=ft.Icon(ft.icons.HUB_ROUNDED, color=th.accent, size=28), alignment=ft.alignment.center, padding=ft.padding.only(bottom=12)),
                    ft.Divider(color="#22222e" if th.is_dark else "#e0e0e8", height=1),
                    rail,
                    ft.Divider(color="#22222e" if th.is_dark else "#e0e0e8", height=1),
                    ft.Container(height=8),
                    ft.Container(alignment=ft.alignment.center, content=profile_btn),
                    ft.Container(height=6),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            content_area
        ], expand=True, spacing=0),
        profile_overlay,
    ])
