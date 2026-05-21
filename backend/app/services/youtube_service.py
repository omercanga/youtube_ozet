from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
import ssl
import os
import logging
import time
from typing import Tuple, Optional, List, Dict
from http.cookiejar import MozillaCookieJar

# --- SSL & Anti-Rate-Limit workaround ---
import urllib.request
import requests
from requests.adapters import HTTPAdapter

# Disable SSL verification globally for urllib
ssl._create_default_https_context = ssl._create_unverified_context

# Browser-like headers to avoid YouTube rate limiting
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5,tr;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Patch requests Session to add browser headers and disable SSL verify
_original_init = requests.Session.__init__
_original_request = requests.Session.request


def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self.headers.update(_BROWSER_HEADERS)


def _patched_request(self, *args, **kwargs):
    kwargs.setdefault("verify", False)
    return _original_request(self, *args, **kwargs)


requests.Session.__init__ = _patched_init
requests.Session.request = _patched_request

# Suppress InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load YouTube cookies if available (Netscape format cookies.txt)
_COOKIES_PATH = os.getenv("YOUTUBE_COOKIES_PATH", "/app/data/cookies.txt")
_cookies = None
if os.path.exists(_COOKIES_PATH):
    try:
        _cookies = MozillaCookieJar(_COOKIES_PATH)
        _cookies.load(ignore_discard=True, ignore_expires=True)
        logging.getLogger(__name__).info(f"Loaded YouTube cookies from {_COOKIES_PATH}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to load cookies: {e}")
        _cookies = None
# --- End workaround ---

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for YouTube video & playlist operations."""

    # --- URL Parsing ---

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
            r"youtube\.com\/watch\?.*v=([^&\n?#]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def extract_playlist_id(url: str) -> Optional[str]:
        """Extract playlist ID from YouTube playlist URL."""
        patterns = [
            r"[?&]list=([^&\n?#]+)",
            r"youtube\.com\/playlist\?list=([^&\n?#]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def is_playlist_url(url: str) -> bool:
        """Check if URL is a playlist URL."""
        return bool(re.search(r"[?&]list=", url))

    # --- Transcript ---

    @staticmethod
    def _get_transcript_via_ytdlp(video_id: str) -> Tuple[str, str]:
        """Fallback: fetch transcript using yt-dlp with browser cookies."""
        import subprocess
        import json as _json
        import tempfile

        logger.info(f"Trying yt-dlp fallback for {video_id}...")

        url = f"https://www.youtube.com/watch?v={video_id}"

        # Try different browser cookie sources
        browser_options = ["chrome", "safari", None]

        for browser in browser_options:
            # Try preferred languages in order
            for lang in ["tr", "en", ""]:
                try:
                    cmd = [
                        "yt-dlp",
                        "--no-download",
                        "--write-subs",
                        "--write-auto-subs",
                        "--sub-format", "json3",
                        "--skip-download",
                        "--no-check-certificates",
                        "--quiet",
                        "--no-warnings",
                    ]

                    # Use browser cookies to authenticate
                    if browser:
                        cmd.extend(["--cookies-from-browser", browser])

                    if lang:
                        cmd.extend(["--sub-langs", lang])
                    else:
                        cmd.extend(["--sub-langs", "all"])

                    with tempfile.TemporaryDirectory() as tmpdir:
                        cmd.extend(["-o", f"{tmpdir}/%(id)s", url])
                        logger.info(f"yt-dlp cmd: browser={browser}, lang={lang}")
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

                        if result.returncode != 0:
                            logger.warning(f"yt-dlp stderr: {result.stderr[:200]}")

                        # Find the subtitle file
                        import glob
                        sub_files = glob.glob(f"{tmpdir}/*.json3")
                        if not sub_files:
                            sub_files = glob.glob(f"{tmpdir}/*.vtt")

                        if sub_files:
                            sub_file = sub_files[0]
                            detected_lang = lang or "unknown"

                            # Try to detect language from filename
                            fname = os.path.basename(sub_file)
                            for code in ["tr", "en", "de", "fr", "es"]:
                                if f".{code}." in fname:
                                    detected_lang = code
                                    break

                            if sub_file.endswith(".json3"):
                                with open(sub_file, "r", encoding="utf-8") as f:
                                    data = _json.load(f)
                                events = data.get("events", [])
                                texts = []
                                for event in events:
                                    segs = event.get("segs", [])
                                    for seg in segs:
                                        text = seg.get("utf8", "").strip()
                                        if text and text != "\n":
                                            texts.append(text)
                                full_text = " ".join(texts)
                            else:
                                # VTT fallback
                                with open(sub_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                import re as _re
                                lines = content.split("\n")
                                texts = []
                                for line in lines:
                                    line = line.strip()
                                    if not line or line.startswith("WEBVTT") or "-->" in line or _re.match(r"^\d+$", line):
                                        continue
                                    clean = _re.sub(r"<[^>]+>", "", line)
                                    if clean:
                                        texts.append(clean)
                                full_text = " ".join(texts)

                            if full_text.strip():
                                logger.info(f"yt-dlp success! browser={browser}, lang={detected_lang}, chars={len(full_text)}")
                                return full_text, detected_lang

                except subprocess.TimeoutExpired:
                    logger.warning(f"yt-dlp timed out (browser={browser})")
                    continue
                except Exception as e:
                    logger.warning(f"yt-dlp failed: browser={browser}, lang={lang}, error={e}")
                    continue

            # If this browser worked for connectivity but no subs found, don't try others
            # (only continue to next browser if there was an error)

        raise Exception("yt-dlp ile de transkript alınamadı.")

    @staticmethod
    def get_transcript(video_id: str, max_retries: int = 2) -> Tuple[str, str]:
        """
        Fetch transcript for a video.
        Tries youtube-transcript-api first, falls back to yt-dlp on rate limiting.
        Returns: (transcript_text, language_code)
        """
        last_error = None

        # --- Attempt 1: youtube-transcript-api ---
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 3 * (2 ** attempt)
                    logger.info(f"Retry {attempt}/{max_retries} for {video_id}, waiting {wait_time}s...")
                    time.sleep(wait_time)

                kwargs = {}
                if _cookies is not None:
                    kwargs["cookies"] = _COOKIES_PATH

                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, **kwargs)

                # Priority: Turkish > English > any available
                transcript = None
                language = "unknown"

                for lang_code in ["tr", "en"]:
                    try:
                        transcript = transcript_list.find_transcript([lang_code])
                        language = lang_code
                        break
                    except Exception:
                        continue

                if transcript is None:
                    try:
                        available = list(transcript_list)
                        if available:
                            transcript = available[0]
                            language = transcript.language_code
                        else:
                            raise Exception("No transcripts available")
                    except Exception:
                        raise Exception("Bu video için transkript bulunamadı.")

                transcript_data = transcript.fetch()
                full_text = " ".join([entry["text"] for entry in transcript_data])
                return full_text, language

            except TranscriptsDisabled:
                raise Exception("Bu video için transkript devre dışı bırakılmış.")
            except NoTranscriptFound:
                raise Exception("Bu video için transkript bulunamadı.")
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "transkript" in error_str:
                    raise
                if "429" in str(e) or "too many requests" in error_str:
                    logger.warning(f"Rate limited (attempt {attempt+1}/{max_retries}): {e}")
                    continue
                raise Exception(f"Transkript alınırken hata oluştu: {str(e)}")

        # --- Attempt 2: yt-dlp fallback ---
        logger.info(f"youtube-transcript-api failed, trying yt-dlp fallback for {video_id}")
        try:
            return YouTubeService._get_transcript_via_ytdlp(video_id)
        except Exception as ytdlp_error:
            logger.error(f"yt-dlp fallback also failed: {ytdlp_error}")
            raise Exception(
                f"Transkript alınamadı. YouTube rate limit aktif. "
                f"Lütfen birkaç dakika bekleyip tekrar deneyin."
            )

    # --- Video Info ---

    @staticmethod
    def get_video_info(video_id: str) -> dict:
        """Get basic video information using oEmbed (no API key needed)."""
        import httpx

        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = httpx.get(url, timeout=10.0, verify=False)
            if response.status_code == 200:
                data = response.json()
                return {
                    "video_id": video_id,
                    "title": data.get("title", f"Video {video_id}"),
                    "author": data.get("author_name", ""),
                }
        except Exception as e:
            logger.warning(f"Could not fetch video info for {video_id}: {e}")

        return {"video_id": video_id, "title": f"Video {video_id}", "author": ""}

    # --- Playlist ---

    @staticmethod
    def get_playlist_videos(playlist_id: str) -> List[Dict]:
        """
        Get list of videos in a playlist using scrapetube.
        Returns list of {video_id, title, duration, thumbnail}
        """
        try:
            import scrapetube

            videos = scrapetube.get_playlist(playlist_id)
            result = []

            for video in videos:
                video_id = video.get("videoId", "")
                title = ""

                # scrapetube returns nested title structure
                title_data = video.get("title", {})
                if isinstance(title_data, dict):
                    runs = title_data.get("runs", [])
                    if runs:
                        title = runs[0].get("text", "")
                    else:
                        title = title_data.get("simpleText", "")
                elif isinstance(title_data, str):
                    title = title_data

                if not title:
                    title = f"Video {video_id}"

                # Duration
                duration = ""
                length_text = video.get("lengthText", {})
                if isinstance(length_text, dict):
                    duration = length_text.get("simpleText", "")

                # Thumbnail
                thumbnail = ""
                thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
                if thumbnails:
                    thumbnail = thumbnails[-1].get("url", "")

                result.append({
                    "video_id": video_id,
                    "title": title,
                    "duration": duration,
                    "thumbnail": thumbnail,
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get playlist videos: {e}")
            raise Exception(f"Oynatma listesi videoları alınamadı: {str(e)}")

    @staticmethod
    def get_playlist_title(playlist_id: str) -> str:
        """Try to get playlist title."""
        try:
            import httpx

            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/playlist?list={playlist_id}&format=json"
            response = httpx.get(url, timeout=10.0, verify=False)
            if response.status_code == 200:
                return response.json().get("title", f"Playlist {playlist_id}")
        except Exception:
            pass
        return f"Playlist {playlist_id}"
