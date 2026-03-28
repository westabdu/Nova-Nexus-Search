# 🌌 Nova Nexus Search: Hibrit AI Derin Araştırma Ekosistemi NOT: BU SİSTEM DEMO SÜRÜMÜDÜR HALA GELİŞTİRİLME AŞAMASINDADIR!!!

**Nova Nexus Search**, standart bir arama motoru değildir. İnternetin gürültüsünü temizleyen, ham veriyi akademik düzeyde analiz eden ve en gelişmiş yapay zeka modellerini bir "Orkestra Şefi" gibi yöneten **akıllı bir bilgi madenciliği istasyonudur.**

![Nova Nexus Logo](https://img.shields.io/badge/Nova_Nexus-v1.0-blueviolet?style=for-the-badge&logo=rocket)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi)
![Flet](https://img.shields.io/badge/Flet-UI-orange?style=for-the-badge&logo=dart)

---

## 🏗️ Sistem Mimarisi ve Karar Mekanizması

Aşağıdaki şema, sistemin çok katmanlı yapısını ve bir sorgunun "Ham Veri"den "Doğrulanmış Rapor"a dönüşüm sürecini profesyonel bir hiyerarşiyle göstermektedir:

```mermaid
graph TB
    %% --- Sinif Tanimlari ---
    classDef frontend fill:#1a1a2e,stroke:#0f3460,stroke-width:2px,color:#fff;
    classDef backend fill:#16213e,stroke:#e94560,stroke-width:2px,color:#fff;
    classDef ai fill:#0f3460,stroke:#533483,stroke-width:3px,color:#fff;
    classDef data fill:#1b1b1b,stroke:#444,stroke-dasharray: 5 5,color:#aaa;
    classDef gold fill:#432818,stroke:#99582a,stroke-width:2px,color:#fff;

    %% --- Giriş ve Seçim ---
    subgraph "🌐 KULLANICI ARAYÜZÜ (CLIENT)"
        UI[("🖥️ Flet Neo-Cyber Dashboard")]
        DEPTH{"🎯 Araştırma Derinliği Seçimi"}
    end

    %% --- Derinlik Mantığı ---
    subgraph "⚡ ARAŞTIRMA MODLARI (LOGIC)"
        SURF["🔹 Yüzeysel (Hızlı)"]
        MED["🔸 Orta (Dengeli)"]
        DEEP["💎 Derin (Detaylı)"]
        ULTRA["🔥 Ultra (Akademik)"]
    end

    %% --- Beyin ve Arama ---
    subgraph "🧠 CORE ENGINE"
        AGENT["🤖 Research Agent (Orchestrator)"]
        QGEN["🔍 Multi-Query Gen"]
        SEARCH["📡 Search Engine (DDGS + Jina)"]
    end

    %% --- Hibrit AI Cluster ---
    subgraph "🔮 DİNAMİK AI YÖNLENDİRİCİ (SMART ROUTER)"
        ROUTE{"🧭 Yük Dengeleyici"}
        L8B["🦙 Llama 3.1 8B (Filter)"]
        L70B["⚔️ Llama 3.3 70B (Synthesis)"]
        GEM["♊ Gemini 1.5 Flash (Big Context)"]
        DSEEK["🧬 DeepSeek Reasoner"]
    end

    %% --- İşleme Akışı ---
    UI --> DEPTH
    DEPTH -->|Yüzeysel: 5 Kaynak| SURF
    DEPTH -->|Orta: 15 Kaynak| MED
    DEPTH -->|Derin: 30 Kaynak| DEEP
    DEPTH -->|Ultra: 50 Kaynak| ULTRA

    SURF & MED & DEEP & ULTRA --> AGENT
    AGENT --> QGEN
    QGEN --> SEARCH
    SEARCH --> ROUTE

    ROUTE -->|Sorgu Filtreleme| L8B
    ROUTE -->|Bağlam < 25K Char| L70B
    ROUTE -->|Bağlam > 25K Char| GEM
    ROUTE -->|Zorlu Mantık Hatası| DSEEK

    L8B & L70B & GEM & DSEEK --> VAL[("🛡️ Sentinel AI Validator")]
    VAL --> FINAL[("📊 Final Premium Rapor")]
    FINAL -.->|WebSocket| UI

    %% --- Atamalar ---
    class UI,DEPTH frontend;
    class SURF,MED,DEEP,ULTRA gold;
    class AGENT,QGEN,SEARCH backend;
    class ROUTE,L8B,L70B,GEM,DSEEK ai;
```

---

## 🌡️ Araştırma Derinliği Seviyeleri

Nova Nexus Search, ihtiyacınıza göre 4 farklı katmanda araştırma yürütebilir. Her katman, harcanan token ve taranan kaynak sayısına göre optimize edilmiştir:

| Mod | Kaynak Sayısı | AI Analiz Gücü | Kullanım Amacı | Hız |
| :--- | :---: | :--- | :--- | :---: |
| **🔹 Yüzeysel** | 5 | Llama 8B | Hızlı cevaplar, kısa tanımlar. | ⚡ Şimşek |
| **🔸 Orta** | 15 | Llama 70B | Genel konu araştırması, ödev hazırlığı. | 🏃 Hızlı |
| **💎 Derin** | 30 | Hybrid (70B & Gemini) | Teknik analiz, detaylı pazar araştırması. | 🧘 Sabırlı |
| **🔥 Ultra** | 50+ | Gemini & DeepSeek | Akademik makale, karşılaştırmalı tez çalışması. | 🐢 Kapsamlı |

---

## ⚡ Akıllı Hibrit Yönlendirme Özelliği

Sistemimiz, tek bir modele bağlı kalmaz. Girdiğiniz verinin boyutuna göre saniyeler içinde karar verir:
*   **Küçük Veri (< 25.000 Karakter):** Dünyanın en iyi denge modeli olan **Llama 3.3 70B**'yi (Groq) kullanır. Hatasız sentez yapar.
*   **Devasa Veri (> 25.000 Karakter):** Llama'nın limitlerini aştığımızda, 1 milyon token hafızalı **Gemini 1.5 Flash** bayrağı devralır. Hiçbir detayı atlamaz.
*   **Karmaşık Sorunlar:** Eğer prompt "Düşünme/Muhakeme" gerektiriyorsa **DeepSeek Reasoner** (Thinking Mode) devreye girerek adım adım mantık yürütür.

---

## 🛠️ Teknik Yetenekler (Packages & Core)

| Bileşen | Teknoloji | Fonksiyonu |
| :--- | :---: | :--- |
| **Backend** | `FastAPI` | Asenkron, yüksek hızda WebSocket ve REST API. |
| **Frontend** | `Flet (Flutter)` | Neon-Cyberpunk temalı, premium masaüstü/web GUI. |
| **Arama** | `DDGS / ddgs` | Reklam engellemeli, sansürsüz DuckDuckGo araması. |
| **Okuyucu** | `Jina Reader` | Web sayfalarını %95 doğrulukla saf metne dönüştürür. |
| **Logging** | `Loguru` | Gerçek zamanlı terminal takibi ve hata yönetimi. |
| **DB** | `SQLite / Alchemy` | Kullanıcı API anahtarları ve araştırma geçmişi arşivi. |

---

## 🚀 Kurulum Rehberi

### 1. Hazırlık
Python 3.12+ kurulu olmalıdır.
```bash
git clone https://github.com/nihai/nova-nexus-search.git
cd nova-nexus-search
```

### 2. Ortamı Kurma (Windows)
```bash
# Sanal ortam oluşturun
python -m venv proje
proje\Scripts\activate

# Bağımlılıkları yükleyin (Ultra Hızlı)
pip install -r requirements.txt
pip install ddgs -U
```

### 3. Yapılandırma
`.env` dosyanızı oluşturun ve anahtarlarınızı girin. Uygulama içindeki **Profil** sekmesinden de anahtarlarınızı canlı olarak güncelleyebilirsiniz.

### 4. Başlatma
```bash
python start.py
```

---

## 🛡️ Sentinel AI Doğrulama Sistemi
Oluşturulan her rapor, **Sentinel AI** adını verdiğimiz bir çapraz kontrol mekanizmasından geçer. Bu modül:
- Yazılan bilgilerin kaynaklarla çelişip çelişmediğini denetler.
- "Halüsinasyon" (AI uydurması) riskini analiz eder.
- Rapora 1-10 arası bir **Güvenilirlik Skoru** atayarak sizi yanıltıcı bilgilerden korur.

---
*Nova Nexus Search - Bilginin Sınırlarını Keşfedin.*
