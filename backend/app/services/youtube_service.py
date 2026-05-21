import re
import ssl
import os
import logging
import time
import random
from typing import Tuple, Optional, List, Dict
from http.cookiejar import MozillaCookieJar

import urllib3
import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

# ── SSL & rate-limit workaround ───────────────────────────────────────────────
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_original_session_init = requests.Session.__init__
_original_session_request = requests.Session.request


def _patched_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    self.headers.update(_BROWSER_HEADERS)


def _patched_request(self, *args, **kwargs):
    kwargs.setdefault("verify", False)
    return _original_session_request(self, *args, **kwargs)


requests.Session.__init__ = _patched_init
requests.Session.request = _patched_request

# ── Cookie yükle ─────────────────────────────────────────────────────────────
_COOKIES_PATH = os.getenv("YOUTUBE_COOKIES_PATH", "/app/data/cookies.txt")
_cookies = None
if os.path.exists(_COOKIES_PATH):
    try:
        _cookies = MozillaCookieJar(_COOKIES_PATH)
        _cookies.load(ignore_discard=True, ignore_expires=True)
        logger.info(f"YouTube cookies loaded from {_COOKIES_PATH}")
    except Exception as e:
        logger.warning(f"Cookie load failed: {e}")

# ── Transcript cache (TTL: 1 saat) ───────────────────────────────────────────
_transcript_cache: Dict[str, Tuple[str, str, float]] = {}  # id → (text, lang, ts)
_CACHE_TTL = 3600


def _cache_get(video_id: str) -> Optional[Tuple[str, str]]:
    entry = _transcript_cache.get(video_id)
    if entry and (time.time() - entry[2]) < _CACHE_TTL:
        logger.info(f"Cache hit for {video_id}")
        return entry[0], entry[1]
    return None


def _cache_set(video_id: str, text: str, lang: str) -> None:
    _transcript_cache[video_id] = (text, lang, time.time())
    # Basit temizlik: 200'den fazla entry varsa en eskiyi sil
    if len(_transcript_cache) > 200:
        oldest = min(_transcript_cache, key=lambda k: _transcript_cache[k][2])
        del _transcript_cache[oldest]


class YouTubeService:

    # ── URL ayrıştırma ────────────────────────────────────────────────────────

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
            r"youtube\.com/watch\?.*v=([^&\n?#]+)",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def extract_playlist_id(url: str) -> Optional[str]:
        m = re.search(r"[?&]list=([^&\n?#]+)", url)
        return m.group(1) if m else None

    @staticmethod
    def is_playlist_url(url: str) -> bool:
        return bool(re.search(r"[?&]list=", url))

    # ── Transkript: Katman 1 — youtube-transcript-api ─────────────────────────

    @staticmethod
    def _fetch_via_yta(video_id: str, max_retries: int = 3) -> Tuple[str, str]:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

        last_err = None
        for attempt in range(max_retries):
            if attempt > 0:
                # Jitter: 2-6s arası random bekle (thundering herd önlemi)
                wait = 2 + random.uniform(0, 4) * attempt
                logger.info(f"YTA retry {attempt}/{max_retries}, waiting {wait:.1f}s...")
                time.sleep(wait)

            try:
                kwargs = {"cookies": _COOKIES_PATH} if _cookies else {}
                tlist = YouTubeTranscriptApi.list_transcripts(video_id, **kwargs)

                for lang in ["tr", "en"]:
                    try:
                        t = tlist.find_transcript([lang])
                        data = t.fetch()
                        text = " ".join(e["text"] for e in data)
                        return text, lang
                    except Exception:
                        continue

                available = list(tlist)
                if available:
                    t = available[0]
                    data = t.fetch()
                    text = " ".join(e["text"] for e in data)
                    return text, t.language_code

                raise NoTranscriptFound(video_id, [], [])

            except TranscriptsDisabled:
                raise Exception("Bu video için transkript devre dışı bırakılmış.")
            except NoTranscriptFound:
                raise Exception("Bu video için transkript bulunamadı.")
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if "transkript" in msg or "disabled" in msg or "found" in msg:
                    raise
                if "429" in str(e) or "too many requests" in msg:
                    logger.warning(f"Rate limited (attempt {attempt+1}): {e}")
                    last_err = e
                    continue
                raise Exception(f"youtube-transcript-api hatası: {e}")

        raise Exception(f"Rate limit aşıldı ({max_retries} deneme). Son hata: {last_err}")

    # ── Transkript: Katman 2 — Supadata API (opsiyonel) ───────────────────────

    @staticmethod
    def _fetch_via_supadata(video_id: str) -> Tuple[str, str]:
        api_key = os.getenv("SUPADATA_API_KEY", "")
        if not api_key:
            raise Exception("SUPADATA_API_KEY tanımlı değil, bu katman atlanıyor.")

        import httpx

        url = "https://api.supadata.ai/v1/youtube/transcript"
        try:
            resp = httpx.get(
                url,
                params={"videoId": video_id, "text": "true"},
                headers={"x-api-key": api_key},
                timeout=20.0,
                verify=False,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Supadata ya "content" (string) ya da "transcript" (list) döndürür
                content = data.get("content") or data.get("transcript", "")
                if isinstance(content, list):
                    content = " ".join(
                        seg.get("text", "") for seg in content if seg.get("text")
                    )
                lang = data.get("lang", "unknown")
                if content.strip():
                    logger.info(f"Supadata success for {video_id}, lang={lang}")
                    return content.strip(), lang
                raise Exception("Supadata boş içerik döndürdü.")
            elif resp.status_code == 404:
                raise Exception("Supadata: transkript bulunamadı.")
            elif resp.status_code == 402:
                raise Exception("Supadata: ücret gerekiyor / kota doldu.")
            else:
                raise Exception(f"Supadata HTTP {resp.status_code}: {resp.text[:100]}")
        except httpx.TimeoutException:
            raise Exception("Supadata zaman aşımı.")

    # ── Transkript: Katman 3 — yt-dlp (son çare) ─────────────────────────────

    @staticmethod
    def _fetch_via_ytdlp(video_id: str) -> Tuple[str, str]:
        import subprocess
        import json as _json
        import tempfile
        import glob

        logger.info(f"yt-dlp fallback başlatılıyor: {video_id}")
        yt_url = f"https://www.youtube.com/watch?v={video_id}"

        # Sadece 2 kombinasyon dene (6'dan düşürüldü), timeout 20s
        attempts = [
            {"browser": "chrome", "langs": "tr,en"},
            {"browser": None,     "langs": "tr,en"},
        ]

        for attempt in attempts:
            try:
                cmd = [
                    "yt-dlp",
                    "--no-download", "--write-subs", "--write-auto-subs",
                    "--sub-format", "json3",
                    "--skip-download", "--no-check-certificates",
                    "--quiet", "--no-warnings",
                    "--sub-langs", attempt["langs"],
                ]
                if attempt["browser"]:
                    cmd.extend(["--cookies-from-browser", attempt["browser"]])

                with tempfile.TemporaryDirectory() as tmpdir:
                    cmd.extend(["-o", f"{tmpdir}/%(id)s", yt_url])
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

                    sub_files = glob.glob(f"{tmpdir}/*.json3") or glob.glob(f"{tmpdir}/*.vtt")
                    if not sub_files:
                        continue

                    sub_file = sub_files[0]
                    fname = os.path.basename(sub_file)
                    lang = next((c for c in ["tr", "en"] if f".{c}." in fname), "unknown")

                    if sub_file.endswith(".json3"):
                        with open(sub_file, encoding="utf-8") as f:
                            data = _json.load(f)
                        texts = [
                            seg.get("utf8", "").strip()
                            for ev in data.get("events", [])
                            for seg in ev.get("segs", [])
                            if seg.get("utf8", "").strip() not in ("", "\n")
                        ]
                    else:
                        import re as _re
                        with open(sub_file, encoding="utf-8") as f:
                            raw = f.read()
                        texts = [
                            _re.sub(r"<[^>]+>", "", line).strip()
                            for line in raw.split("\n")
                            if line.strip()
                            and not line.startswith("WEBVTT")
                            and "-->" not in line
                            and not _re.match(r"^\d+$", line.strip())
                        ]
                        texts = [t for t in texts if t]

                    full_text = " ".join(texts)
                    if full_text.strip():
                        logger.info(f"yt-dlp success: browser={attempt['browser']}, lang={lang}")
                        return full_text, lang

            except subprocess.TimeoutExpired:
                logger.warning(f"yt-dlp timeout: browser={attempt['browser']}")
            except Exception as e:
                logger.warning(f"yt-dlp error: browser={attempt['browser']}, {e}")

        raise Exception("yt-dlp ile de transkript alınamadı.")

    # ── Ana transkript metodu ─────────────────────────────────────────────────

    @staticmethod
    def get_transcript(video_id: str) -> Tuple[str, str]:
        """
        Transkript çekme — 3 katmanlı fallback zinciri:
        1. youtube-transcript-api (jitter + retry)
        2. Supadata API           (SUPADATA_API_KEY set ise)
        3. yt-dlp                 (son çare, optimize edilmiş)
        Cache: video_id başına 1 saat TTL
        """
        cached = _cache_get(video_id)
        if cached:
            return cached

        errors = []

        # Katman 1: youtube-transcript-api
        try:
            text, lang = YouTubeService._fetch_via_yta(video_id)
            _cache_set(video_id, text, lang)
            return text, lang
        except Exception as e:
            msg = str(e)
            if "devre dışı" in msg or "bulunamadı" in msg:
                raise  # Kesin başarısız, fallback'e gerek yok
            errors.append(f"YTA: {msg}")
            logger.warning(f"YTA failed, trying fallbacks: {msg}")

        # Katman 2: Supadata API (opsiyonel)
        if os.getenv("SUPADATA_API_KEY"):
            try:
                text, lang = YouTubeService._fetch_via_supadata(video_id)
                _cache_set(video_id, text, lang)
                return text, lang
            except Exception as e:
                errors.append(f"Supadata: {e}")
                logger.warning(f"Supadata failed: {e}")

        # Katman 3: yt-dlp
        try:
            text, lang = YouTubeService._fetch_via_ytdlp(video_id)
            _cache_set(video_id, text, lang)
            return text, lang
        except Exception as e:
            errors.append(f"yt-dlp: {e}")

        raise Exception(
            "Transkript alınamadı. Tüm yöntemler denendi:\n" + "\n".join(errors)
        )

    # ── Video bilgisi ─────────────────────────────────────────────────────────

    @staticmethod
    def get_video_info(video_id: str) -> dict:
        import httpx
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = httpx.get(url, timeout=10.0, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "video_id": video_id,
                    "title": data.get("title", f"Video {video_id}"),
                    "author": data.get("author_name", ""),
                }
        except Exception as e:
            logger.warning(f"Video info fetch failed for {video_id}: {e}")
        return {"video_id": video_id, "title": f"Video {video_id}", "author": ""}

    # ── Playlist ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_playlist_videos(playlist_id: str) -> List[Dict]:
        try:
            import scrapetube
            result = []
            for video in scrapetube.get_playlist(playlist_id):
                vid = video.get("videoId", "")
                title_data = video.get("title", {})
                if isinstance(title_data, dict):
                    runs = title_data.get("runs", [])
                    title = runs[0].get("text", "") if runs else title_data.get("simpleText", "")
                else:
                    title = str(title_data)
                title = title or f"Video {vid}"

                duration = ""
                lt = video.get("lengthText", {})
                if isinstance(lt, dict):
                    duration = lt.get("simpleText", "")

                thumbnail = ""
                thumbs = video.get("thumbnail", {}).get("thumbnails", [])
                if thumbs:
                    thumbnail = thumbs[-1].get("url", "")

                result.append({"video_id": vid, "title": title, "duration": duration, "thumbnail": thumbnail})
            return result
        except Exception as e:
            logger.error(f"Playlist fetch failed: {e}")
            raise Exception(f"Oynatma listesi videoları alınamadı: {e}")

    @staticmethod
    def get_playlist_title(playlist_id: str) -> str:
        try:
            import httpx
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/playlist?list={playlist_id}&format=json"
            resp = httpx.get(url, timeout=10.0, verify=False)
            if resp.status_code == 200:
                return resp.json().get("title", f"Playlist {playlist_id}")
        except Exception:
            pass
        return f"Playlist {playlist_id}"
