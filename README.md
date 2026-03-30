# 🌌 Nova Nexus Search: Hibrit AI Derin Araştırma Ekosistemi

**Nova Nexus Search**, standart bir arama motoru değildir. İnternetin gürültüsünü temizleyen, ham veriyi akademik düzeyde analiz eden ve en gelişmiş **OpenRouter** yapay zeka modellerini bir "Orkestra Şefi" gibi yöneten, tamamen **ücretsiz modeller üzerine inşa edilmiş akıllı bir bilgi madenciliği istasyonudur.**

![Nova Nexus Logo](https://img.shields.io/badge/Nova_Nexus-v2.0-blueviolet?style=for-the-badge&logo=rocket)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi)
![Flet](https://img.shields.io/badge/Flet-UI-orange?style=for-the-badge&logo=dart)

---

> [!CAUTION]
> ### ⚠️ KRİTİK UYARI / DISCLAIMER (ÖNEMLİ)
> 
> **🧪 Erken Test Aşamasında (Alpha/Beta):** Bu sistem aktif geliştirme ve test aşamasındadır. Kapsamlı bir "Hata (Bug)" barındırma ihtimali yüksektir. Sistem, zaman zaman beklemeyen çökmeler yaşayabilir.
>
> **🌍 Dil Desteği Sınırlaması:** Sistem altyapı olarak **12 dil desteğine** (Promptlar, yerelleştirmeler ve çeviriler) sahip olmakla birlikte, aktif olarak sadece **Türkçe ve İngilizce** dillerinde detaylıca test edilmiştir. Diğer dillerde kullanırken ekstra hatalar veya dil kaymaları gözlemleyebilirsiniz.
> 
> **🧠 Halüsinasyon Riski:** Yapay zeka ajanları, nadiren de olsa veriler arasında yanlış bağlantılar kurabilir veya "Halüsinasyon" (gerçek dışı bilgi üretimi) yaşayabilir. **Sentinel AI** doğrulama sistemimiz bu riski minimize etse de, rapor edilen bilgileri kritik işlerinizde her zaman manuel olarak çapraz kontrolden geçirmeniz **hayati önem taşır.**
> 
> **⚖️ Sorumluluk Sınırı:** Bu yazılımın kullanımı sırasında oluşabilecek herhangi bir veri kaybı, API kotası tüketimi, maddi/manevi zarar veya üretilen yalan bilgilerin kullanımından **Geliştirici sorumlu tutulamaz**. Yazılım ticari bir ürün olmayıp "olduğu gibi" (As-Is) sunulmaktadır.

---

## 🏗️ Sistem Mimarisi ve Tek API Stratejisi

Nova Nexus v2 ile birlikte parçalı altyapılar (Groq, Gemini, DeepSeek vb.) terk edilmiş ve tamamen **OpenRouter** merkezli bir "Hiyerarşik Yedekleme (Fallback)" sistemine geçilmiştir:

1. **Filtreleme Ajanı (`liquid/lfm`)**: Gelen web verilerini ışık hızında okur ve alakasız olanları eler.
2. **Birincil Sentez Ajanı (`openai/gpt-oss-120b:free`)**: Ana raporlama işlemlerini gerçekleştiren, deha düzeyindeki 120 Milyar parametrelik beyindir.
3. **Yedek Zeka (Fallback) Ajanları**: Ana model yoğunluktan dolayı kota verirse veya yorulursa, sistem beklemeksizin `minimax-m2.5`, `dolphin-mistral` ve son çare olarak `nemotron` modellerine zıplayarak raporun yarıda kalmasını önler.

---

## 🚀 Kurulum Rehberi (Adım Adım)

Projenin kendi bilgisayarınızda (Özel Server) ayağa kaldırılması oldukça basittir. 

### 1. Gereksinimleri Hazırlama
Bilgisayarınızda **Python 3.12** veya üstü yüklü olmalıdır.

```bash
# Projeyi cihazınıza çekin
git clone https://github.com/nihai/nova-nexus-search.git
cd nova-nexus-search
```

### 2. Sanal Ortam (Virtual Environment) Kurulumu
Çakışmaları önlemek için projeyi kendi izole ortamında kurmanızı tavsiye ederiz.

```bash
# Windows
python -m venv proje
proje\Scripts\activate

# Linux / MacOS
python3 -m venv proje
source proje/bin/activate
```

### 3. Paketleri Yükleme
```bash
# Gerekli tüm kütüphaneleri (FastAPI, Flet, OpenRouter SDK, PDF oluşturucular) yükleyin
pip install -r requirements.txt

# (Opsiyonel) PDF çıktısı alırken hatalarla karşılaşırsanız kütüphaneyi tazeleyin:
pip install xhtml2pdf -U
```

### 4. Yapılandırma (\`.env\` Ayarları)
Veritabanı ve AI Anahtarı tanımlaması. Proje dizininde (ana klasörde) `.env` adında bir dosya oluşturun veya var olanı düzenleyin:

```env
# SADECE BU ANAHTAR YETERLİDİR (https://openrouter.ai/)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxx

# Uygulama Güvenlik Tokeni (Rastgele harf-rakam yazabilirsiniz)
SECRET_KEY=nova_super_secret_key_1234
```

---

## 💻 Çalıştırma ve Kullanım

### Başlatma
Her şey kurulduğunda uygulamayı (Backend ve Flet UI) tek bir merkezi komutla başlatabilirsiniz:
```bash
python start.py
```
> Ekranda önce *Backend Uvicorn* başlatılacak, ardından büyüleyici bir Neo-Cyberpunk ekran (MacOS/Win11 cam efekti) açılacaktır.

### İlk Kullanım
1. Açılan pencerede **"Hesap Oluştur"** kısmına gelin.
2. Basit bir e-posta, Kullanıcı Adı ve Şifre bilgisi girin. Yeni mimari kapsamında, OpenRouter API kutucuğu kayıt ekranından istendiği takdirde doldurulabilir veya daha sonra arayüz üzerinden işlenebilir.
3. Kayıt olduktan sonra, "Ayarlar" panelinden kendi profilinize has API anahtarlarınızı da güncelleyebilirsiniz.

---

## 🛡️ Sentinel AI Doğrulama Sistemi

Oluşturulan her rapor, ek olarak **Sentinel AI** adını verdiğimiz bir çapraz kontrol mekanizmasından geçer. Bu modül:
- Yazılan bilgilerin kaynaklarla çelişip çelişmediğini denetler. Makalelerin linkini size [Kaynak 1] formatıyla referans gösterir.
- "Halüsinasyon" riskini analiz eder ve size rapora ne kadar güvenebileceğinizi söyler (Örn: 9/10).
- Tüm verileri isteğinize göre (MD, HTML, PDF, JSON) derleyerek indirebilmenizi sağlar.

---
*Nova Nexus Search - Bilginin Gürültüsünden Arınmış Saf Gerçekliğe.*
