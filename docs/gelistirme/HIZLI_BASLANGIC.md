# 🚀 Hızlı Başlangıç Kılavuzu

## Ön Gereksinimler

1. **Docker ve Docker Compose** yüklü olmalı
2. **OpenAI API Key** (https://platform.openai.com/api-keys)

## 3 Adımda Başlat

### 1️⃣ Environment Ayarları

```bash
# .env dosyası oluştur
cp .env.example .env

# .env dosyasını düzenle ve API key'ini ekle
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2️⃣ Uygulamayı Başlat

```bash
# Tüm servisleri başlat (ilk çalıştırma 5-10 dakika sürebilir)
docker-compose up --build
```

### 3️⃣ Kullanmaya Başla

Tarayıcınızda açın: **http://localhost:5173**

## 🎯 İlk Kullanım

1. YouTube video URL'si girin (örnek: https://www.youtube.com/watch?v=dQw4w9WgXcQ)
2. "Analiz Et" butonuna tıklayın
3. Birkaç saniye bekleyin
4. Özet ve prompt'u görüntüleyin!

## 📍 Önemli URL'ler

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Dokümantasyonu:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

## 🛑 Durdurma

```bash
# Servisleri durdur
docker-compose down

# Veritabanı dahil her şeyi temizle
docker-compose down -v
```

## ⚠️ Sık Karşılaşılan Sorunlar

### Port zaten kullanımda
```bash
# Çalışan container'ları kontrol et
docker ps

# Eski container'ları temizle
docker-compose down
```

### OpenAI API hatası
- API key'inizin doğru olduğundan emin olun
- API limitinizi kontrol edin: https://platform.openai.com/usage

### Video transkripti bulunamadı
- Bazı videolarda transkript olmayabilir
- Farklı bir video deneyin

## 💡 İpuçları

- İlk çalıştırmada Docker image'ları indirilecek (biraz zaman alır)
- Kod değişiklikleri otomatik yansır (hot-reload)
- Veritabanı verileri kalıcıdır (docker-compose down -v ile silinir)

## 📊 Test Videoları

Transkripti olan popüler videolar:
- TED Talks
- Eğitim videoları
- Konferans kayıtları
- Podcast'ler

## 🆘 Yardım

Sorun yaşıyorsanız:
1. `docker-compose logs` ile logları kontrol edin
2. `docker-compose down -v && docker-compose up --build` ile temiz başlatın
3. README.md dosyasına bakın
4. PROJE_DURUMU.md dosyasını inceleyin
