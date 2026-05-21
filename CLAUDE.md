# youtube_ozet — Geliştirme Kuralları

## Proje Nedir
YouTube transkript çeken ve AI ile analiz eden web uygulaması.
Hedef: Freemium SaaS (başlangıçta auth yok, IP tabanlı rate limit).

## Mimari

```
backend/  → FastAPI (Python 3.11) + SQLAlchemy + SQLite/PostgreSQL
frontend/ → React 18 + Vite + TailwindCSS
AI        → OpenRouter API (openai kütüphanesi ile)
Deploy    → Docker Compose
```

Portlar: Backend 8001→8000, Frontend 5180→5173.

## Temel Kurallar

### Backend
- Tüm endpoint'ler `async def` olmalı. Sync endpoint ekleme.
- Tüm yeni DB kolonları `nullable=True` olmalı (migration sistemi yok, tablo auto-create).
- `print()` kullanma; sadece `logger.error/warning/info()` kullan.
- Environment variable hardcode etme; `.env.example`'ı güncelle.
- `MAX_TRANSCRIPT_CHARS` her zaman env var'dan oku, sabit değer yazma.

### AI Analiz Sistemi (openai_service.py)
- AI'dan daima **sadece JSON** iste; markdown/serbest metin kabul etme.
- Her yeni alan için `_parse_json_response`'a varsayılan değer ekle.
- Faktüel analiz için temperature 0.3–0.5, yaratıcı çıktı için 0.7.
- Her iki analiz metodu da (`analyze_transcript`, `analyze_playlist_combined`) aynı alan setini döndürmeli.
- `required_keys` listesi sistem promptundaki JSON şemasıyla senkronize tutulmalı.

### Yeni Analiz Alanı Eklerken Kontrol Listesi
1. `models.py` → `nullable=True` kolonu ekle
2. `schemas.py` → `AnalyzeResponse` ve `HistoryDetail`'e ekle
3. `openai_service.py` → sistem prompt JSON şemasına ekle + `required_keys`'e ekle + return dict'e ekle
4. `routers/api.py` → her `VideoAnalysis(...)` çağrısında yeni alanı ekle (3 yer var)
5. `frontend/src/components/ResultDisplay.jsx` → görsel bileşeni ekle
6. `frontend/src/i18n/locales/tr.json` ve `en.json` → çeviri anahtarını ekle

### Frontend
- CSS framework değiştirme; sadece TailwindCSS kullan.
- Bileşenler `src/components/`, servisler `src/services/` altında kalmalı.
- API çağrılarını `src/services/api.js`'e ekle, bileşenler içinde doğrudan axios kullanma.

## Mevcut Analiz Alanları

| Alan | Tip | Açıklama |
|------|-----|----------|
| `summary` | Text | Kısa özet (3-5 cümle) |
| `video_summary` | Text | Detaylı özet (1-2 paragraf) |
| `generated_prompt` | Text | Kısa AI prompt önerisi |
| `detailed_prompt` | Text | Uzun AI prompt önerisi |
| `keywords` | Text | Virgüllü anahtar kelimeler |
| `content_type` | String(100) | İçerik sınıflandırması |
| `target_audience` | String(200) | Hedef kitle |
| `sentiment` | String(100) | Duygu tonu + kısa açıklama |
| `key_quotes` | Text | JSON array — öne çıkan alıntılar |
| `action_items` | Text | Satır ayrımlı aksiyon maddeleri |
| `difficulty_level` | String(50) | Başlangıç / Orta / İleri |
| `one_liner` | String(300) | Tek cümlelik elevator pitch |

## Freemium SaaS Yol Haritası

### Faz 1 — Şimdi (Auth Yok)
- IP tabanlı günlük limit: 5 ücretsiz analiz
- Upstash Redis veya DB'de IP+tarih sayacı
- LemonSqueezy ile kredi satışı (10 kredi = $3 gibi)

### Faz 2 — Auth Ekle
- Supabase Auth (magic link + Google OAuth)
- Kullanıcı başına analiz geçmişi
- Pro plan: $9/ay → sınırsız analiz
- Team plan: $29/ay → API erişimi

### Faz 3 — API Marketplace
- RapidAPI'de listele
- Webhook desteği ekle
- Bulk analiz endpoint'i

## Güvenlik Notları
- `OPENROUTER_API_KEY` commit'leme. `.gitignore`'da mevcut.
- Mevcut key ifşa oldu — `https://openrouter.ai/keys` adresinden yenile.
- SSL verification kapalı (`verify=False`). Production'da düzelt.
- CORS `*` sadece dev için; prod'da kısıtla.

## YouTube Servis Kuralları
- Önce `youtube-transcript-api`, fallback olarak `yt-dlp`.
- Dil önceliği: Türkçe (tr) > İngilizce (en) > ilk mevcut.
- Playlist maksimum 15 video (abuse önlemi) — değiştirme.

## Bağımlılık Yönetimi
- Yeni Python paketi eklerken `requirements.txt`'i güncelle.
- Yeni Node paketi eklerken `package.json`'ı güncelle.
- `yt-dlp` ağır; gerçekten gerekmedikçe import etme.
