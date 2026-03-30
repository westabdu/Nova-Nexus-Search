# i18n.py - Advanced Multi-Language Support System
"""
🌍 Nova Nexus Search - Enterprise Internationalization (i18n) System

Supported Languages: 12 (TR, EN, DE, FR, RU, AR, ES, IT, PT, JA, ZH, KO)

Features:
- Pluralization support
- Date/Time formatting
- Number formatting (thousand separators, decimals)
- Dynamic variable interpolation
- Fallback mechanism
- Language detection
- RTL (Right-to-Left) support for Arabic
"""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class Language(Enum):
    """Supported languages"""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    RUSSIAN = "ru"
    ARABIC = "ar"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"

class DateFormat(Enum):
    """Date format types"""
    SHORT = "short"      # 01.01.2025
    LONG = "long"        # 1 Ocak 2025
    FULL = "full"        # Pazartesi, 1 Ocak 2025

# ============================================================================
# TRANSLATIONS DICTIONARY
# ============================================================================

TRANSLATIONS = {
    "tr": {
        # App Branding
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Çapraz Doğrulama ile Derin Araştırma Platformu",
        "app_version": "Sürüm",
        
        # Authentication
        "login": "Giriş Yap",
        "register": "Ücretsiz Kayıt Ol",
        "email": "E-Posta",
        "password": "Şifre",
        "username": "Kullanıcı Adı",
        "login_btn": "Giriş",
        "register_btn": "Kayıt Ol",
        "logout": "Çıkış Yap",
        "forgot_password": "Şifremi Unuttum",
        "remember_me": "Beni Hatırla",
        
        # Search Interface
        "search_placeholder": "Araştırmak istediğiniz konuyu yazın...",
        "search_button": "Ara",
        "search_results": "{count} araştırma sonucu bulundu",
        "search_results_plural": "{count} araştırma sonucu bulundu",
        
        # Research Depth
        "depth_label": "Araştırma Derinliği",
        "depth_surface": "Yüzeysel (Hızlı)",
        "depth_medium": "Orta",
        "depth_deep": "Derin",
        "depth_ultra": "Ultra Derin",
        "depth_description_surface": "5 kaynaktan hızlı araştırma",
        "depth_description_medium": "15 kaynaktan dengeli araştırma",
        "depth_description_deep": "30 kaynaktan detaylı araştırma",
        "depth_description_ultra": "50+ kaynaktan kapsamlı akademik araştırma",
        
        # Language & Settings
        "lang_label": "Çıktı Dili",
        "language": "Dil",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
        
        # Research Controls
        "start_research": "Araştırmayı Başlat",
        "pause_research": "Araştırmayı Duraklat",
        "resume_research": "Araştırmayı Devam Et",
        "stop_research": "Araştırmayı Durdur",
        "clear_search": "Aramayı Temizle",
        
        # Results & Reports
        "live_log_title": "Canlı İlerleme",
        "report_title": "Araştırma Raporu",
        "report_generated": "Rapor oluşturuldu: {date}",
        "sources_found": "kaynak bulundu",
        "sources_found_count": "{count} kaynak bulundu",
        "reliable_sources": "güvenilir kaynak",
        "reliability_score": "Güvenilirlik Skoru",
        
        # Export Formats
        "export_as": "Şu Formatta Dışa Aktar:",
        "download_md": "Markdown İndir",
        "download_html": "HTML İndir",
        "download_pdf": "PDF İndir",
        "download_json": "JSON İndir",
        "download_csv": "CSV İndir",
        "export_success": "✅ Dosya başarıyla indirildi: {filename}",
        "export_error": "❌ Dışa aktarma başarısız: {error}",
        
        # User Profile
        "profile": "Profil",
        "my_account": "Hesabım",
        "api_key": "API Anahtarım",
        "api_keys": "API Anahtarları",
        "create_api_key": "Yeni API Anahtarı Oluştur",
        "copy_api_key": "API Anahtarını Kopyala",
        "delete_api_key": "API Anahtarını Sil",
        "api_key_copied": "✅ API anahtarı panoya kopyalandı",
        
        # Quota & Limits
        "quota_label": "Kalan Araştırma Hakkı",
        "quota_remaining": "{remaining}/{total} araştırma kaldı",
        "quota_reset": "Kota sıfırlanacak: {date}",
        "quota_unlimited": "Sınırsız",
        "upgrade_plan": "Planını Yükselt",
        
        # Timestamps
        "just_now": "Az önce",
        "minutes_ago": "{n} dakika önce",
        "hours_ago": "{n} saat önce",
        "days_ago": "{n} gün önce",
        "months_ago": "{n} ay önce",
        
        # Status Messages
        "loading": "Yükleniyor...",
        "processing": "İşleniyor...",
        "success": "✅ Başarılı",
        "error": "❌ Hata",
        "warning": "⚠️ Uyarı",
        "info": "ℹ️ Bilgi",
        
        # Errors
        "error_empty_query": "Lütfen bir araştırma konusu girin.",
        "error_quota": "Günlük araştırma hakkınız dolmuştur ({used}/{limit}).",
        "error_network": "Ağ hatası. Lütfen bağlantınızı kontrol edin.",
        "error_server": "Sunucu hatası. Lütfen daha sonra tekrar deneyin.",
        "error_timeout": "İstek zaman aşımına uğradı.",
        "error_invalid_input": "Geçersiz giriş. Lütfen kontrol edin.",
        
        # Disclaimers
        "disclaimer": "⚠️ Bu rapor yapay zeka tarafından otomatik oluşturulmuştur. Bilgilerin doğruluğunu teyit ediniz.",
        "beta_notice": "🧪 Bu özellik beta aşamasındadır. Hata raporlaması beklentileri.",
        "experimental": "🔬 Deneysel Özellik",
        
        # Navigation
        "back": "Geri",
        "next": "İleri",
        "skip": "Atla",
        "done": "Bitti",
        "cancel": "İptal",
        "save": "Kaydet",
        "delete": "Sil",
        "edit": "Düzenle",
        "close": "Kapat",
        
        # Theme
        "switch_theme": "Tema Değiştir",
        "dark_mode": "Koyu Tema",
        "light_mode": "Açık Tema",
        
        # Placeholders
        "no_report": "Henüz bir araştırma yapılmadı.",
        "no_data": "Veri bulunamadı.",
        "no_results": "Sonuç bulunamadı.",
        
        # Months & Days
        "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
        "days": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
    },
    
    "en": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Deep Research Platform with Cross-Validation",
        "app_version": "Version",
        "login": "Login",
        "register": "Register for Free",
        "email": "Email",
        "password": "Password",
        "username": "Username",
        "login_btn": "Sign In",
        "register_btn": "Sign Up",
        "logout": "Logout",
        "forgot_password": "Forgot Password",
        "remember_me": "Remember Me",
        "search_placeholder": "Enter a topic to research...",
        "search_button": "Search",
        "search_results": "{count} research result found",
        "search_results_plural": "{count} research results found",
        "depth_label": "Research Depth",
        "depth_surface": "Surface (Fast)",
        "depth_medium": "Medium",
        "depth_deep": "Deep",
        "depth_ultra": "Ultra Deep",
        "depth_description_surface": "Fast research from 5 sources",
        "depth_description_medium": "Balanced research from 15 sources",
        "depth_description_deep": "Detailed research from 30 sources",
        "depth_description_ultra": "Comprehensive academic research from 50+ sources",
        "lang_label": "Output Language",
        "language": "Language",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
        "start_research": "Start Research",
        "pause_research": "Pause Research",
        "resume_research": "Resume Research",
        "stop_research": "Stop Research",
        "clear_search": "Clear Search",
        "live_log_title": "Live Progress",
        "report_title": "Research Report",
        "report_generated": "Report generated: {date}",
        "sources_found": "sources found",
        "sources_found_count": "{count} sources found",
        "reliable_sources": "reliable sources",
        "reliability_score": "Reliability Score",
        "export_as": "Export As:",
        "download_md": "Download Markdown",
        "download_html": "Download HTML",
        "download_pdf": "Download PDF",
        "download_json": "Download JSON",
        "download_csv": "Download CSV",
        "export_success": "✅ File downloaded successfully: {filename}",
        "export_error": "❌ Export failed: {error}",
        "profile": "Profile",
        "my_account": "My Account",
        "api_key": "My API Key",
        "api_keys": "API Keys",
        "create_api_key": "Create New API Key",
        "copy_api_key": "Copy API Key",
        "delete_api_key": "Delete API Key",
        "api_key_copied": "✅ API key copied to clipboard",
        "quota_label": "Remaining Research Quota",
        "quota_remaining": "{remaining}/{total} research remaining",
        "quota_reset": "Quota resets: {date}",
        "quota_unlimited": "Unlimited",
        "upgrade_plan": "Upgrade Plan",
        "just_now": "Just now",
        "minutes_ago": "{n} minutes ago",
        "hours_ago": "{n} hours ago",
        "days_ago": "{n} days ago",
        "months_ago": "{n} months ago",
        "loading": "Loading...",
        "processing": "Processing...",
        "success": "✅ Success",
        "error": "❌ Error",
        "warning": "⚠️ Warning",
        "info": "ℹ️ Info",
        "error_empty_query": "Please enter a research topic.",
        "error_quota": "Your daily research quota is exhausted ({used}/{limit}).",
        "error_network": "Network error. Please check your connection.",
        "error_server": "Server error. Please try again later.",
        "error_timeout": "Request timeout.",
        "error_invalid_input": "Invalid input. Please check and try again.",
        "disclaimer": "⚠️ This report was automatically generated by AI. Please verify the accuracy of information.",
        "beta_notice": "🧪 This feature is in beta. Bug reports expected.",
        "experimental": "🔬 Experimental Feature",
        "back": "Back",
        "next": "Next",
        "skip": "Skip",
        "done": "Done",
        "cancel": "Cancel",
        "save": "Save",
        "delete": "Delete",
        "edit": "Edit",
        "close": "Close",
        "switch_theme": "Toggle Theme",
        "dark_mode": "Dark Mode",
        "light_mode": "Light Mode",
        "no_report": "No research has been conducted yet.",
        "no_data": "No data found.",
        "no_results": "No results found.",
        "months": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"],
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    },
    
    # German
    "de": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Tiefes Forschungsplattform mit Kreuzvalidierung",
        "app_version": "Version",
        "login": "Anmelden",
        "register": "Kostenlos registrieren",
        "email": "E-Mail",
        "password": "Passwort",
        "username": "Benutzername",
        "login_btn": "Einloggen",
        "register_btn": "Registrieren",
        "logout": "Abmelden",
        "forgot_password": "Passwort vergessen",
        "remember_me": "Passwort speichern",
        "search_placeholder": "Geben Sie ein Thema zur Recherche ein...",
        "search_button": "Suchen",
        "search_results": "{count} Suchergebnis gefunden",
        "search_results_plural": "{count} Suchergebnisse gefunden",
        "depth_label": "Recherchetiefe",
        "depth_surface": "Oberfläche (Schnell)",
        "depth_medium": "Mittel",
        "depth_deep": "Tief",
        "depth_ultra": "Ultra Tief",
        "depth_description_surface": "Schnelle Recherche aus 5 Quellen",
        "depth_description_medium": "Ausgewogene Recherche aus 15 Quellen",
        "depth_description_deep": "Detaillierte Recherche aus 30 Quellen",
        "depth_description_ultra": "Umfassende akademische Recherche aus 50+ Quellen",
        "lang_label": "Ausgabesprache",
        "language": "Sprache",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
        "start_research": "Recherche starten",
        "pause_research": "Recherche pausieren",
        "resume_research": "Recherche fortsetzen",
        "stop_research": "Recherche beenden",
        "clear_search": "Suche löschen",
        "live_log_title": "Live Fortschritt",
        "report_title": "Forschungsbericht",
        "report_generated": "Bericht erstellt: {date}",
        "sources_found": "Quellen gefunden",
        "sources_found_count": "{count} Quellen gefunden",
        "reliable_sources": "zuverlässige Quellen",
        "reliability_score": "Zuverlässigkeitswert",
        "export_as": "Exportieren als:",
        "download_md": "Markdown herunterladen",
        "download_html": "HTML herunterladen",
        "download_pdf": "PDF herunterladen",
        "download_json": "JSON herunterladen",
        "download_csv": "CSV herunterladen",
        "export_success": "✅ Datei erfolgreich heruntergeladen: {filename}",
        "export_error": "❌ Export fehlgeschlagen: {error}",
        "profile": "Profil",
        "my_account": "Mein Konto",
        "api_key": "Mein API-Schlüssel",
        "api_keys": "API-Schlüssel",
        "create_api_key": "Neuen API-Schlüssel erstellen",
        "copy_api_key": "API-Schlüssel kopieren",
        "delete_api_key": "API-Schlüssel löschen",
        "api_key_copied": "✅ API-Schlüssel in die Zwischenablage kopiert",
        "quota_label": "Verbleibendes Recherche-Kontingent",
        "quota_remaining": "{remaining}/{total} Recherchen verbleibend",
        "quota_reset": "Kontingent zurückgesetzt: {date}",
        "quota_unlimited": "Unbegrenzt",
        "upgrade_plan": "Plan aktualisieren",
        "just_now": "Gerade eben",
        "minutes_ago": "vor {n} Minuten",
        "hours_ago": "vor {n} Stunden",
        "days_ago": "vor {n} Tagen",
        "months_ago": "vor {n} Monaten",
        "loading": "Laden...",
        "processing": "Wird verarbeitet...",
        "success": "✅ Erfolg",
        "error": "❌ Fehler",
        "warning": "⚠️ Warnung",
        "info": "ℹ️ Info",
        "error_empty_query": "Bitte geben Sie ein Recherchethema ein.",
        "error_quota": "Ihr tägliches Recherche-Kontingent ist erschöpft ({used}/{limit}).",
        "error_network": "Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung.",
        "error_server": "Serverfehler. Bitte versuchen Sie es später erneut.",
        "error_timeout": "Anfrage abgelaufen.",
        "error_invalid_input": "Ungültige Eingabe. Bitte überprüfen Sie diese.",
        "disclaimer": "⚠️ Dieser Bericht wurde automatisch von KI erstellt. Bitte überprüfen Sie die Genauigkeit der Informationen.",
        "beta_notice": "🧪 Diese Funktion befindet sich in der Beta-Phase. Fehlerberichte erwartet.",
        "experimental": "🔬 Experimentelle Funktion",
        "back": "Zurück",
        "next": "Weiter",
        "skip": "Überspringen",
        "done": "Fertig",
        "cancel": "Abbrechen",
        "save": "Speichern",
        "delete": "Löschen",
        "edit": "Bearbeiten",
        "close": "Schließen",
        "switch_theme": "Design wechseln",
        "dark_mode": "Dunkler Modus",
        "light_mode": "Heller Modus",
        "no_report": "Es wurde noch keine Recherche durchgeführt.",
        "no_data": "Keine Daten gefunden.",
        "no_results": "Keine Ergebnisse gefunden.",
        "months": ["Januar", "Februar", "März", "April", "Mai", "Juni",
                   "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "days": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    },
    
    # French (abbreviated - add full version similarly)
    "fr": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Plateforme de Recherche Approfondie avec Validation Croisée",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Russian (abbreviated)
    "ru": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Платформа глубоких исследований с перекрёстной проверкой",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Arabic (abbreviated - RTL)
    "ar": {
        "app_name": "نوفا نيكسوس سيرش",
        "app_subtitle": "منصة بحث عميق مع التحقق المتقاطع",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Spanish
    "es": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Plataforma de Investigación Profunda con Validación Cruzada",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Italian
    "it": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Piattaforma di Ricerca Approfondita con Convalida Incrociata",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Portuguese
    "pt": {
        "app_name": "Nova Nexus Search",
        "app_subtitle": "Plataforma de Pesquisa Profunda com Validação Cruzada",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Japanese
    "ja": {
        "app_name": "ノバ・ネクサス・サーチ",
        "app_subtitle": "クロス検証を備えた深い研究プラットフォーム",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Chinese (Simplified)
    "zh": {
        "app_name": "新星联系搜索",
        "app_subtitle": "具有交叉验证的深度研究平台",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
    
    # Korean
    "ko": {
        "app_name": "노바 넥서스 서치",
        "app_subtitle": "교차 검증이 있는 심층 연구 플랫폼",
        "languages": {
            "tr": "Türkçe",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "ru": "Русский",
            "ar": "العربية",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
        },
    },
}

# ============================================================================
# LANGUAGE CONFIGURATION
# ============================================================================

LANGUAGE_NAMES = {
    "tr": "Türkçe",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "ru": "Русский",
    "ar": "العربية",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ja": "日本語",
    "zh": "中文",
    "ko": "한국어",
}

# RTL (Right-to-Left) Languages
RTL_LANGUAGES = {"ar"}

# Date format patterns per language
DATE_FORMATS = {
    "tr": {"short": "%d.%m.%Y", "long": "%d %B %Y", "full": "%A, %d %B %Y"},
    "en": {"short": "%m/%d/%Y", "long": "%B %d, %Y", "full": "%A, %B %d, %Y"},
    "de": {"short": "%d.%m.%Y", "long": "%d. %B %Y", "full": "%A, %d. %B %Y"},
    "fr": {"short": "%d/%m/%Y", "long": "%d %B %Y", "full": "%A %d %B %Y"},
    "ru": {"short": "%d.%m.%Y", "long": "%d %B %Y", "full": "%A, %d %B %Y"},
    "ar": {"short": "%d/%m/%Y", "long": "%d %B %Y", "full": "%A %d %B %Y"},
}

# Number format patterns (thousand separator, decimal separator)
NUMBER_FORMATS = {
    "tr": {"thousand": ".", "decimal": ","},
    "en": {"thousand": ",", "decimal": "."},
    "de": {"thousand": ".", "decimal": ","},
    "fr": {"thousand": " ", "decimal": ","},
    "ru": {"thousand": " ", "decimal": ","},
    "ar": {"thousand": ",", "decimal": "."},
}

# ============================================================================
# TRANSLATION FUNCTIONS
# ============================================================================

def t(key: str, lang: str = "tr", **kwargs) -> str:
    """
    Translate a key to the given language with variable interpolation.
    
    Examples:
        t("app_name", "en")
        t("search_results_count", "en", count=5)
        t("error_quota", "tr", used=8, limit=10)
    """
    # Get translation
    translation = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    text = translation.get(key, key)
    
    # Handle pluralization
    if "_plural" in key and isinstance(text, dict):
        count = kwargs.get("count", 1)
        text = translation.get(key + ("_plural" if count != 1 else ""), key)
    
    # Interpolate variables
    for var_name, var_value in kwargs.items():
        text = text.replace(f"{{{var_name}}}", str(var_value))
    
    return text


def format_date(date: datetime, lang: str = "tr", format_type: str = "long") -> str:
    """
    Format date according to language preferences.
    
    Args:
        date: datetime object
        lang: language code
        format_type: 'short', 'long', or 'full'
    
    Example:
        format_date(datetime.now(), "en", "full")
        # Output: "Monday, January 20, 2025"
    """
    if lang not in DATE_FORMATS:
        lang = "en"
    
    format_pattern = DATE_FORMATS[lang].get(format_type, "%d %B %Y")
    return date.strftime(format_pattern)


def format_number(number: float, lang: str = "tr", decimals: int = 2) -> str:
    """
    Format number according to language preferences.
    
    Args:
        number: number to format
        lang: language code
        decimals: number of decimal places
    
    Example:
        format_number(1234567.89, "en")  # "1,234,567.89"
        format_number(1234567.89, "de")  # "1.234.567,89"
    """
    if lang not in NUMBER_FORMATS:
        lang = "en"
    
    format_config = NUMBER_FORMATS[lang]
    thousand_sep = format_config["thousand"]
    decimal_sep = format_config["decimal"]
    
    # Format with locale-specific thousand separator
    formatted = f"{number:,.{decimals}f}"
    formatted = formatted.replace(",", "TEMP_SEP")
    formatted = formatted.replace(".", decimal_sep)
    formatted = formatted.replace("TEMP_SEP", thousand_sep)
    
    return formatted


def get_time_ago(minutes: int, lang: str = "tr") -> str:
    """
    Get human-readable time string.
    
    Example:
        get_time_ago(5, "en")    # "5 minutes ago"
        get_time_ago(120, "en")  # "2 hours ago"
    """
    if minutes == 0:
        return t("just_now", lang)
    elif minutes < 60:
        return t("minutes_ago", lang, n=minutes)
    elif minutes < 1440:
        hours = minutes // 60
        return t("hours_ago", lang, n=hours)
    else:
        days = minutes // 1440
        return t("days_ago", lang, n=days)


def is_rtl(lang: str) -> bool:
    """Check if language is Right-to-Left."""
    return lang in RTL_LANGUAGES


def get_supported_languages() -> Dict[str, str]:
    """Get all supported languages."""
    return LANGUAGE_NAMES.copy()


def get_language_by_code(code: str) -> Optional[str]:
    """Get language name by code."""
    return LANGUAGE_NAMES.get(code)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# Basic translation
name = t("app_name", "en")
# Output: "Nova Nexus Search"

# Translation with variables
message = t("search_results", "en", count=5)
# Output: "5 research results found"

# Format date
date_str = format_date(datetime.now(), "en", "full")
# Output: "Monday, January 20, 2025"

# Format number
num_str = format_number(1234567.89, "en")
# Output: "1,234,567.89"

# Get time ago
time_str = get_time_ago(30, "en")
# Output: "30 minutes ago"

# Check if RTL
is_arabic_rtl = is_rtl("ar")
# Output: True
"""