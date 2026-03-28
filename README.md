# 🌌 Nova Nexus Search: Hibrit AI Derin Araştırma Ekosistemi

**Nova Nexus Search**, klasik arama motorlarının ötesine geçerek interneti bir bilgi madeni gibi kazıyan, verileri doğrulayan ve en gelişmiş yapay zeka modelleriyle sentezleyen **yeni nesil bir hibrit araştırma motorudur.**

![Nova Nexus Logo](https://img.shields.io/badge/Nova_Nexus-v1.0-blueviolet?style=for-the-badge&logo=rocket)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi)
![Flet](https://img.shields.io/badge/Flet-UI-orange?style=for-the-badge&logo=dart)

---

## 🏗️ Sistem Mimarisi ve Çalışma Şeması

Aşağıdaki şema, bir arama sorgusunun başlangıcından raporun kullanıcıya ulaştığı ana kadar izlediği yolu göstermektedir:

```mermaid
graph TB
    %% --- Sinif Tanimlari (Profesyonel Renk Paleti) ---
    classDef frontend fill:#1a1a2e,stroke:#0f3460,stroke-width:2px,color:#fff;
    classDef backend fill:#16213e,stroke:#e94560,stroke-width:2px,color:#fff;
    classDef ai fill:#0f3460,stroke:#533483,stroke-width:3px,color:#fff;
    classDef external fill:#1b1b1b,stroke:#444,stroke-dasharray: 5 5,color:#aaa;
    classDef validator fill:#1b4332,stroke:#2d6a4f,stroke-width:2px,color:#fff;

    %% --- Katman 1: Kullanici Etkilesimi ---
    subgraph "🌐 CLIENT INTERFACE"
        UI[("🖥️ Flet Neo-Cyber Dashboard")]
        WS_M["🔌 Real-time WS Manager"]
    end

    %% --- Katman 2: Beyin (Backend) ---
    subgraph "🧠 CORE INTELLIGENCE"
        AGENT["🤖 Research Agent (Orchestrator)"]
        QGEN["🔍 Multi-Query Generator"]
        CLEAN["🧹 Markdown Content Purifier"]
    end

    %% --- Katman 3: Veri Kaynaklari ---
    subgraph "📡 EXTERNAL DATA MINING"
        DDGS["🦆 DuckDuckGo Engine"]
        JINA["📄 Jina Reader PDF/Web"]
        FALL["🌐 HTTPx Fallback"]
    end

    %% --- Katman 4: Yapay Zeka Hibrit Katmani ---
    subgraph "⚡ HYBRID AI CLUSTER (Routing Logic)"
        ROUTER{"🧭 AI Model Router"}
        LLAMA_S["🦙 Llama 3.1 8B (Fast Filter)"]
        LLAMA_L["⚔️ Llama 3.3 70B (Synthesis)"]
        GEMINI["♊ Gemini 1.5 Flash (Long Context)"]
        DEEP["🧬 DeepSeek Reasoner (Logic)"]
    end

    %% --- Katman 5: Kalite Kontrol ---
    subgraph "🛡️ QUALITY ASSURANCE"
        VAL["✅ Sentinel Validator"]
        REP["📊 Report Generator (PDF/MD)"]
    end

    %% --- Akis Baglantilari ---
    UI -->|Sorgu Gönder| WS_M
    WS_M <--> AGENT
    AGENT --> QGEN
    QGEN --> DDGS
    DDGS --> JINA
    JINA --> CLEAN
    CLEAN --> ROUTER

    ROUTER -.->|Token < 25K| LLAMA_L
    ROUTER -.->|Token > 25K| GEMINI
    ROUTER -.->|Hizli Süzme| LLAMA_S
    ROUTER -.->|Muhakeme| DEEP

    LLAMA_L & GEMINI & LLAMA_S & DEEP --> VAL
    VAL --> REP
    REP -.->|Final Yanit| WS_M

    %% --- Stil Atamalari ---
    class UI,WS_M frontend;
    class AGENT,QGEN,CLEAN backend;
    class ROUTER,LLAMA_S,LLAMA_L,GEMINI,DEEP ai;
    class DDGS,JINA,FALL external;
    class VAL,REP validator;
```

---

## 🔍 Bir Araştırma Nasıl Gerçekleşir? (Adım Adım)

1.  **Sorgu Analizi:** Kullanıcı arama yaptığında, sistem önce konuyu analiz eder ve en iyi sonuçları almak için 3-5 adet teknik alt sorgu üretir.
2.  **Bilgi Toplama:** DuckDuckGo üzerinden tüm dünya çapında tarama yapılır. Bulunan her URL, **Jina Reader** kullanılarak reklam/bannerlardan arındırılmış saf Markdown metnine dönüştürülür.
3.  **Hibrit Filtreleme (Hız):** Toplanan onlarca kaynak, **Llama 3.1 8B** (Groq) üzerinden saniyeler içinde taranır. Sadece konuyla en alakalı olan en iyi 15 kaynak seçilir.
4.  **Akıllı Yönlendirme (Router):** 
    *   Eğer toplam veri **25.000 karakterden az** ise **Llama 3.3 70B** kullanılır (Yüksek doğruluk).
    *   Eğer veri **25.000 karakterden fazla** ise devasa hafızasıyla **Gemini 1.5 Flash** devreye girer.
5.  **Doğrulama (Sentinel):** Yazılan rapor son bir kez "Çapraz Kontrole" girer. Yapay zeka kendi yazdığı rapordaki çelişkileri denetler ve bir **Güvenilirlik Skoru** üretir.
6.  **Arşivleme:** Tüm süreç `nova_nexus.db` (SQLite) veritabanına kaydedilir ve kullanıcıya anlık WebSocket üzerinden iletilir.

---

## 🛠️ Gerekli Paketler ve Teknoloji Yığını

Uygulamanın çalışması için aşağıdaki kritik kütüphaneler kullanılmaktadır:

| Paket | Görevi |
| :--- | :--- |
| **fastapi / uvicorn** | Yüksek performanslı asenkron API sunucusu ve WebSocket yönetimi. |
| **flet** | Flutter tabanlı, Python ile yazılmış modern ve dinamik kullanıcı arayüzü. |
| **ddgs (duckduckgo_search)** | Ücretsiz ve gizlilik odaklı web araması yapmayı sağlar. |
| **httpx** | Jina Reader ve diğer dış servislere asenkron HTTP istekleri atmak için. |
| **loguru** | Gelişmiş, renkli ve dosya tabanlı hata takip sistemi (Logging). |
| **sqlalchemy** | Veritabanı (SQLite) yönetimi ve ORM işlemleri. |
| **pydantic v2** | Veri tipi doğrulama ve JSON şemalarının yönetimi. |
| **groq / google-generativeai / openai** | AI modelleriyle iletişim kuran resmi SDK'lar. |

---

## 🚀 Kurulum ve Çalıştırma

### 1. Dosya Hazırlığı
Bilgisayarınızda Python 3.12 yüklü olduğundan emin olun.
```bash
git clone https://github.com/nihai/nova-nexus-search.git
cd nova-nexus-search
```

### 2. Bağımlılık Karargahı
```bash
# Sanal ortam oluşturma
python -m venv proje
source proje/bin/activate  # Windows: proje\Scripts\activate

# Paketleri yükleme
pip install -r requirements.txt
pip install ddgs -U  # Arama modülünü güncel tutun
```

### 3. Anahtar Yapılandırması (.env)
Aşağıdaki gibi bir `.env` dosyası oluşturun:
```env
JWT_SECRET=nexus_secret_key_123
DATABASE_URL=sqlite:///./nova_nexus.db
# API Anahtarlarınızı isterseniz buraya isterseniz uygulama içine girin
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
```

### 4. Ateşleme
```bash
python start.py
```

---

## 🛡️ Güvenlik ve Gizlilik
*   **Kişisel Anahtarlar:** API anahtarları veritabanında saklanır ancak her kullanıcı sadece kendi anahtarını kullanır.
*   **Oturum Güvenliği:** JWT tabanlı token sistemi ve 2FA (Çift Faktörlü Doğrulama) desteği altyapıda mevcuttur.

---
*Nova Nexus Search - Veriyi Bilgiye, Bilgiyi Güce Dönüştürün.*
