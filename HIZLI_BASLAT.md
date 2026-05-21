# 🚀 Hızlı Başlangıç

## Projeyi Çalıştırma (3 Adım)

### 1. Docker Container'ları Başlat
```bash
docker-compose up --build
```

İlk çalıştırmada build işlemi 5-10 dakika sürebilir. Sonraki çalıştırmalarda daha hızlı olacak.

### 2. Uygulamaya Eriş

Tarayıcınızda şu adresleri açın:

- **Frontend (Ana Uygulama):** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Dokümantasyonu:** http://localhost:8000/docs

### 3. Test Et

1. YouTube video URL'si girin (örnek: https://www.youtube.com/watch?v=dQw4w9WgXcQ)
2. "Analiz Et" butonuna tıklayın
3. Özet ve prompt'u görüntüleyin
4. Geçmiş kayıtları kontrol edin

## ✅ Başarılı Çalışma Kontrolleri

Container'ların durumunu kontrol edin:
```bash
docker-compose ps
```

Hepsi "Up" durumunda olmalı:
- youtube_analyzer_db
- youtube_analyzer_backend
- youtube_analyzer_frontend

## 🛑 Durdurma

```bash
docker-compose down
```

Veritabanı verilerini de silmek için:
```bash
docker-compose down -v
```

## 🔧 Sorun Giderme

### Port zaten kullanımda hatası
Başka bir uygulama aynı portları kullanıyor olabilir. docker-compose.yml dosyasındaki portları değiştirin:
- Frontend: 5173 → 3000
- Backend: 8000 → 8080
- Database: 5432 → 5433

### Container başlamıyor
```bash
docker-compose down -v
docker-compose up --build
```

### Backend hatası
Backend loglarını kontrol edin:
```bash
docker-compose logs backend
```

### Frontend hatası
Frontend loglarını kontrol edin:
```bash
docker-compose logs frontend
```

## 📝 Önemli Notlar

- ✅ OpenRouter API key zaten .env dosyasında tanımlı
- ✅ Google Gemini 2.0 Flash (ücretsiz) model kullanılıyor
- ✅ Türkçe dil desteği aktif
- ✅ PostgreSQL verileri kalıcı (volume kullanılıyor)

## 🎯 Test Videoları

Transkripti olan Türkçe videolar:
- TED Talks Türkçe
- Eğitim videoları
- Podcast'ler

Not: Tüm YouTube videolarında transkript bulunmayabilir. Transkript yoksa uygulama bunu bildirecektir.

## 🔄 Geliştirme Modu

Kod değişiklikleriniz otomatik olarak yansıyacaktır (hot-reload aktif):
- Frontend: React Fast Refresh
- Backend: Uvicorn auto-reload

Değişiklik yaptıktan sonra tarayıcıyı yenilemeniz yeterli.

## 📊 Veritabanı Yönetimi

PostgreSQL'e bağlanmak için:
```bash
docker exec -it youtube_analyzer_db psql -U postgres -d youtube_analyzer
```

Tabloları görmek:
```sql
\dt
SELECT * FROM video_analyses;
```

## 🎉 Başarılı!

Artık YouTube videolarından transkript çekip AI ile analiz edebilirsiniz!
