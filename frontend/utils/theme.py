"""
Theme Manager - Koyu ve Açık Tema Renk Paletleri
"""

class Theme:
    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.update()

    def update(self):
        if self.is_dark:
            self.bg = "#050a14"               # Ana arka plan
            self.surface = "#0d1117"          # Panel arkaplanı
            self.surface_variant = "#162036"  # Hafif açık panel/buton arkaplanı
            self.border = "#1e293b"           # Kenarlık
            self.border_focus = "#00d4ff"     # Odaklanılan kenarlık (mavi)
            
            self.text_main = "#e2e8f0"        # Ana metin
            self.text_dim = "#94a3b8"         # İkincil metin (soluk)
            self.text_muted = "#475569"       # Pasif metin
            
            self.accent = "#00d4ff"           # Ana vurgu rengi
            self.success = "#22c55e"          # Başarılı
            self.warning = "#f59e0b"          # Uyarı
            self.error = "#ef4444"            # Hata
            self.error_bg = "#2d0000"         # Hata zemin
            self.success_bg = "#0d3321"       # Başarı zemin
            self.accent_bg = "#1e3a5f"        # Vurgu zemin
        else:
            self.bg = "#f1f5f9"               # Açık ana arka plan
            self.surface = "#ffffff"          # Pane arkaplanı
            self.surface_variant = "#e2e8f0"  # Hafif koyu panel/buton
            self.border = "#cbd5e1"           # Kenarlık
            self.border_focus = "#0284c7"     # Odaklanılan kenarlık (koyu mavi)
            
            self.text_main = "#0f172a"        # Ana metin
            self.text_dim = "#334155"         # İkincil metin
            self.text_muted = "#64748b"       # Pasif metin
            
            self.accent = "#0284c7"           # Vurgu rengi (Light Blue)
            self.success = "#16a34a"          # Başarılı
            self.warning = "#d97706"          # Uyarı
            self.error = "#dc2626"            # Hata
            self.error_bg = "#fee2e2"         # Hata zemin
            self.success_bg = "#bbf7d0"       # Başarı zemin
            self.accent_bg = "#e0f2fe"        # Vurgu zemin

current_theme = Theme(is_dark=True)
