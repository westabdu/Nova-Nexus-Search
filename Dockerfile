# Nova Nexus Search - Dockerfile
FROM python:3.11-slim

# Gerekli sistem paketlerini yükle (PDF ve bağımlılıklar için)
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm kodları kopyala
COPY . .

# Flet Web üzerinden yayın yapmak için 8550 portu açılır
# (FastAPI backend ise 8000'de kendi içinde veya Flet handler üzerinden döner)
EXPOSE 8550
EXPOSE 8000

# start.py'yi çalıştır
# Container içindeyken "flet_web" modunu argüman olarak verebiliriz,
# ama start.py varsayılan flet app olarak kalkıyor, bunu docker-compose.yml içinden env ile ayarlayabiliriz.
CMD ["python", "start.py"]
