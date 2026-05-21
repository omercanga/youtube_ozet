# YouTube Video Transkript Analiz Uygulaması - PRD

## Proje Özeti
YouTube video linkinden otomatik transkript çeken, AI ile analiz edip özet ve prompt üreten web uygulaması.

## Teknik Stack
- **Backend:** Python 3.11 + FastAPI
- **Frontend:** React 18 + Vite + TailwindCSS
- **Database:** PostgreSQL 15
- **AI Service:** OpenRouter API (Google Gemini 2.0 Flash - ücretsiz)
- **Transkript:** youtube-transcript-api
- **Containerization:** Docker + Docker Compose

## Temel Özellikler

### 1. Video Transkript Çekme
- YouTube video URL'si girişi
- Otomatik video ID çıkarma
- Transkript indirme (Türkçe/İngilizce öncelikli)
- Hata yönetimi (transkript yoksa bilgilendirme)

### 2. AI Analiz ve Özet
- Transkript'i OpenAI API'ye gönderme
- Kısa özet oluşturma (3-5 cümle)
- İlgili prompt önerisi oluşturma
- Türkçe çıktı

### 3. Veritabanı Kayıt
- Her analiz kaydını saklama
- Kayıt bilgileri:
  - Video URL
  - Video başlığı
  - Transkript metni
  - Oluşturulan özet
  - Oluşturulan prompt
  - Oluşturulma tarihi

### 4. Geçmiş Görüntüleme
- Tüm analizleri listeleme
- Tarih, video başlığı ile filtreleme
- Detay görüntüleme

## API Endpoints

### Backend (FastAPI)
```
POST   /api/analyze          - Video analiz et
GET    /api/history          - Geçmiş kayıtları getir
GET    /api/history/{id}     - Tek kayıt detayı
DELETE /api/history/{id}     - Kayıt sil
GET    /api/health           - Health check
```

## Veritabanı Şeması

### Table: video_analyses
```sql
id              SERIAL PRIMARY KEY
video_url       VARCHAR(500) NOT NULL
video_id        VARCHAR(50) NOT NULL
video_title     VARCHAR(500)
transcript_text TEXT NOT NULL
summary         TEXT NOT NULL
generated_prompt TEXT NOT NULL
language        VARCHAR(10)
created_at      TIMESTAMP DEFAULT NOW()
```

## Proje Yapısı
```
youtube-transcript-analyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # DB connection
│   │   ├── services/
│   │   │   ├── youtube_service.py
│   │   │   └── openai_service.py
│   │   └── routers/
│   │       └── api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── AnalyzeForm.jsx
│   │   │   ├── ResultDisplay.jsx
│   │   │   └── HistoryList.jsx
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Geliştirme Görevleri (Spec-Driven)

### Spec 1: Proje Altyapısı
- [ ] Docker compose yapılandırması
- [ ] PostgreSQL container setup
- [ ] Backend container setup
- [ ] Frontend container setup
- [ ] Environment variables

### Spec 2: Backend - Database & Models
- [ ] SQLAlchemy models
- [ ] Pydantic schemas
- [ ] Database connection
- [ ] Migration setup

### Spec 3: Backend - YouTube Service
- [ ] Video ID extraction
- [ ] Transcript fetching
- [ ] Error handling

### Spec 4: Backend - OpenAI Service
- [ ] OpenAI client setup
- [ ] Prompt engineering (özet + prompt üretimi)
- [ ] API integration

### Spec 5: Backend - API Endpoints
- [ ] POST /api/analyze
- [ ] GET /api/history
- [ ] GET /api/history/{id}
- [ ] DELETE /api/history/{id}

### Spec 6: Frontend - UI Components
- [ ] Video URL input form
- [ ] Loading states
- [ ] Result display
- [ ] History list
- [ ] Error handling

### Spec 7: Integration & Testing
- [ ] Frontend-Backend integration
- [ ] Docker compose test
- [ ] End-to-end test

## Çevre Değişkenleri
```
OPENROUTER_API_KEY=sk-or-v1-...
DATABASE_URL=postgresql://user:pass@db:5432/youtube_analyzer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=youtube_analyzer
```

## Başarı Kriterleri
- ✅ YouTube linkinden transkript çekebilme
- ✅ AI ile özet ve prompt üretebilme
- ✅ Veritabanına kayıt edebilme
- ✅ Geçmiş kayıtları görüntüleyebilme
- ✅ Docker ile tek komutla çalıştırabilme

## Zaman Tahmini
- Toplam: ~4-6 saat
- Backend: 2-3 saat
- Frontend: 1-2 saat
- Docker & Integration: 1 saat
