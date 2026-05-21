# YouTube Transkript Analiz

YouTube video ve oynatma listelerinden otomatik transkript çeken, AI ile derinlemesine analiz eden dockerize web uygulaması.

## Özellikler

- YouTube URL, manuel transkript ve oynatma listesi analizi
- AI ile 12 farklı çıktı: özet, kapsamlı özet, anahtar kelime açıklamaları, duygu tonu, zorluk seviyesi, alıntılar, aksiyon maddeleri, AI prompt önerileri ve daha fazlası
- Sonuç kartında 5 sekme: Genel Bakış / Kapsamlı Özet / Anahtar Kelimeler / AI Prompts / Alıntılar & Aksiyonlar
- Türkçe ve İngilizce arayüz desteği
- Geçmiş analizleri görüntüleme, detay inceleme ve silme
- Docker ile tek komutla kurulum

## Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Frontend | React 18, Vite, TailwindCSS |
| Veritabanı | SQLite (geliştirme), PostgreSQL (üretim) |
| AI | OpenRouter API — model `.env` ile seçilebilir |
| Container | Docker, Docker Compose |

## Kurulum

### Gereksinimler

- Docker ve Docker Compose
- [OpenRouter](https://openrouter.ai) API Key

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone <repo-url>
cd youtube_ozet

# 2. Ortam dosyasını oluşturun
cp .env.example .env

# 3. .env içine OpenRouter API key'inizi ekleyin
# OPENROUTER_API_KEY=sk-or-v1-...

# 4. Başlatın
docker compose up --build
```

Uygulama adresleri:
- **Frontend:** http://localhost:5180
- **Backend API:** http://localhost:8001
- **Swagger Docs:** http://localhost:8001/docs

## Kullanım

### YouTube URL
1. YouTube sekmesine video URL'sini yapıştırın
2. "Analiz Et" butonuna tıklayın
3. Sonuçlar 5 sekmede görüntülenir

### Manuel Transkript
Elinizde hazır bir transkript varsa Manuel sekmesinden doğrudan analiz edebilirsiniz.

### Oynatma Listesi
Playlist sekmesinden bir oynatma listesi URL'si girin, videoları seçin ve ayrı ayrı veya toplu analiz edin.

## Analiz Çıktıları

| Alan | Açıklama |
|------|----------|
| `one_liner` | Tek cümlelik elevator pitch |
| `summary` | 5-7 cümlelik kısa özet |
| `video_summary` | Tüm konuları kapsayan bölümlü kapsamlı özet |
| `keywords` | 8-12 anahtar kelime etiketi |
| `keyword_summary` | Her kelimenin videodaki bağlamı ve önemi |
| `sentiment` | Duygu tonu (Pozitif / Negatif / Nötr) |
| `difficulty_level` | Başlangıç / Orta / İleri |
| `content_type` | İçerik sınıflandırması |
| `target_audience` | Hedef kitle tanımı |
| `key_quotes` | 3-5 öne çıkan alıntı |
| `action_items` | Somut aksiyon maddeleri |
| `generated_prompt` / `detailed_prompt` | AI prompt önerileri |

## API Endpoints

```
POST /api/analyze                   # YouTube URL analizi
POST /api/analyze-manual            # Manuel transkript analizi
GET  /api/playlist/info?url=...     # Playlist video listesi
POST /api/playlist/analyze          # Playlist analizi
GET  /api/history                   # Tüm geçmiş analizler
GET  /api/history/{id}              # Tek analiz detayı
DELETE /api/history/{id}            # Analiz sil
```

## Ortam Değişkenleri

```env
OPENROUTER_API_KEY=sk-or-v1-...          # Zorunlu
AI_MODEL=openai/gpt-3.5-turbo            # Model seçimi
DATABASE_URL=sqlite:////app/data/app.db  # DB bağlantısı
MAX_TRANSCRIPT_CHARS=8000                # AI'a gönderilen max karakter
CORS_ORIGINS=*                           # CORS ayarı
```

## Proje Yapısı

```
youtube_ozet/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── services/
│   │   │   ├── openai_service.py   # AI analiz + prompt'lar
│   │   │   └── youtube_service.py  # Transkript çekme
│   │   └── routers/
│   │       └── api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ResultDisplay.jsx   # 5 sekmeli sonuç kartı
│   │   │   ├── AnalyzeForm.jsx
│   │   │   ├── ManualAnalyzeForm.jsx
│   │   │   ├── PlaylistForm.jsx
│   │   │   └── HistoryList.jsx
│   │   ├── services/api.js
│   │   ├── i18n/                   # TR / EN çeviriler
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                       # Geliştirme kuralları
└── README.md
```

## Sorun Giderme

**Container'ları sıfırdan başlatmak:**
```bash
docker compose down
docker compose up --build
```

**Mevcut DB'yi koruyarak yeniden başlatmak:**
```bash
docker compose restart
```

**Container içinde DB migration:**
```bash
docker exec <backend_container> python3 -c "
import sqlite3; conn = sqlite3.connect('/app/data/app.db')
# ALTER TABLE komutlarını buraya ekleyin
conn.commit(); conn.close()
"
```

## Lisans

MIT