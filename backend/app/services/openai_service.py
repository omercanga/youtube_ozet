from openai import OpenAI
import os
import json
import re
import logging
import httpx

logger = logging.getLogger(__name__)

_SINGLE_VIDEO_SYSTEM_PROMPT = """Sen uzman bir video içerik analiz asistanısın.
Verilen transkripti derinlemesine analiz et ve aşağıdaki JSON'u üret.
SADECE geçerli JSON döndür. Başka metin, yorum veya markdown ekleme.

ÖNEMLİ — DİL KURALI:
{lang_instruction}

{
  "one_liner": "Videonun tek cümlelik özü. Sosyal medyada paylaşılabilir, 15-20 kelimeyi geçmez.",
  "summary": "5-7 cümlelik kısa özet. Ana fikir, temel iddialar, öne çıkan argümanlar ve sonuç dahil.",
  "video_summary": "Transkriptteki TÜM konuları ve önemli noktaları kapsayan kapsamlı özet. Konuşmanın kronolojik akışını takip et. Her ana konuyu '## Konu Başlığı' formatında ayrı bir başlık altında işle. Hiçbir önemli bilgiyi, örneği veya açıklamayı atlama. Uzunluk konu sayısına ve derinliğe göre değişmeli — eksik bırakma, fazla özet yapma. Transkriptte geçen somut örnekler, rakamlar ve alıntılar varsa bunları koru.",
  "keywords": "Virgülle ayrılmış 8-12 anahtar kelime. Genel değil, bu videoya özgü terimler seç.",
  "keyword_summary": "Her anahtar kelimenin bu videodaki bağlamını ve önemini açıkla. Her kelime için '**kelime**: açıklama' formatında ayrı satır kullan. Açıklama 1-2 cümle olmalı — kelimenin videoda neden önemli olduğunu ve nasıl kullanıldığını anlat.",
  "content_type": "İçerik türü: Eğitim, Haber, Eğlence, Tutorial, Röportaj, Tartışma, Motivasyon, Belgesel, Podcast, Yorum",
  "target_audience": "Hedef kitleyi 1 cümleyle tanımla. Yaş, ilgi alanı, bilgi seviyesi gibi özellikleri belirt.",
  "difficulty_level": "Başlangıç veya Orta veya İleri — içeriğin gerektirdiği ön bilgiye göre belirle.",
  "sentiment": "Genel duygu tonu: Pozitif, Negatif veya Nötr — ardından kısa bir açıklama (max 10 kelime).",
  "key_quotes": ["Transkriptten alınan 3-5 dikkat çekici alıntı. Birebir cümle tercih et.", "..."],
  "action_items": "Videonun izleyiciye önerdiği somut adımlar. Her madde ayrı satırda, '- ' ile başlasın. Yoksa boş bırak.",
  "prompt": "Bu videoyu AI'a özetletmek için kısa prompt (1-2 cümle).",
  "detailed_prompt": "Bağlamı, amacı ve beklenen çıktıyı içeren detaylı AI prompt önerisi (3-5 cümle)."
}"""

_PLAYLIST_SYSTEM_PROMPT = """Sen uzman bir video serisi analiz asistanısın.
Bir oynatma listesindeki birden fazla videonun transkriptleri verilmiştir.
Tümünü bir bütün olarak analiz et ve aşağıdaki JSON'u üret.
SADECE geçerli JSON döndür. Başka metin, yorum veya markdown ekleme.

ÖNEMLİ — DİL KURALI:
{lang_instruction}

{
  "one_liner": "Oynatma listesinin tek cümlelik özü. 15-20 kelimeyi geçmez.",
  "summary": "5-7 cümlelik genel özet. Serinin amacı, kapsadığı konular, hedefi ve öne çıkan temalar.",
  "video_summary": "Her videonun katkısını ve aralarındaki bağlantıyı kapsayan kapsamlı seri özeti. Her videoyu '## Video N: Başlık' formatında ayrı başlık altında işle. Her videonun ana konularını, önemli noktalarını ve öğretilerini ayrıntılı anlat. Serinin genel akışını ve bütünlüğünü son bir bölümde değerlendir.",
  "keywords": "Tüm seriyi kapsayan virgüllü 10-15 anahtar kelime.",
  "keyword_summary": "Her anahtar kelimenin serideki bağlamını açıkla. '**kelime**: açıklama' formatında ayrı satırlar. Kelimenin seri boyunca nasıl işlendiğini 1-2 cümleyle anlat.",
  "content_type": "Seri türü: Eğitim Serisi, Kurs, Belgesel Serisi, Podcast Serisi, Tutorial Serisi, vb.",
  "target_audience": "Hedef kitleyi 1 cümleyle tanımla.",
  "difficulty_level": "Başlangıç veya Orta veya İleri",
  "sentiment": "Genel duygu tonu: Pozitif, Negatif veya Nötr — ardından kısa açıklama.",
  "key_quotes": ["Seriden 3-5 öne çıkan alıntı veya fikir.", "..."],
  "action_items": "Serinin izleyiciye önerdiği adımlar. Her madde ayrı satırda, '- ' ile başlasın. Yoksa boş bırak.",
  "prompt": "Bu seriyi AI'a özetletmek için kısa prompt.",
  "detailed_prompt": "Seri kapsamını, öğrenme hedeflerini ve beklenen çıktıyı içeren detaylı prompt."
}"""

_LANG_INSTRUCTIONS = {
    "tr": "Tüm çıktıları Türkçe yaz. Teknik terimler ve özel isimler orijinal dilinde kalabilir.",
    "en": "Write all outputs in English. Technical terms and proper nouns may stay in their original language.",
}


def _build_prompt(template: str, ui_lang: str) -> str:
    instruction = _LANG_INSTRUCTIONS.get(ui_lang[:2].lower(), _LANG_INSTRUCTIONS["tr"])
    return template.replace("{lang_instruction}", instruction)


_REQUIRED_KEYS = [
    "one_liner", "summary", "video_summary", "prompt", "detailed_prompt",
    "keywords", "keyword_summary", "content_type", "target_audience", "sentiment",
    "key_quotes", "action_items", "difficulty_level",
]


class OpenAIService:

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        http_client = httpx.Client(timeout=90.0, verify=False)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            http_client=http_client,
        )
        self.model = os.getenv("AI_MODEL", "openai/gpt-3.5-turbo")

    def _parse_json_response(self, content: str) -> dict:
        try:
            result = json.loads(content)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except json.JSONDecodeError:
                pass

        brace_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse JSON from AI response: {content[:200]}...")
        return {key: "" for key in _REQUIRED_KEYS}

    def _normalize_result(self, raw: dict) -> dict:
        key_quotes = raw.get("key_quotes", [])
        if isinstance(key_quotes, list):
            key_quotes_str = json.dumps(key_quotes, ensure_ascii=False)
        else:
            key_quotes_str = str(key_quotes)

        action_items = raw.get("action_items", "")
        if isinstance(action_items, list):
            action_items = "\n".join(f"- {i}" for i in action_items if i)
        elif not isinstance(action_items, str):
            action_items = str(action_items)

        def _to_str(val):
            if val is None:
                return ""
            if isinstance(val, (list, dict)):
                return json.dumps(val, ensure_ascii=False)
            return str(val)

        return {
            "one_liner": _to_str(raw.get("one_liner")),
            "summary": _to_str(raw.get("summary")) or "Özet oluşturulamadı",
            "video_summary": _to_str(raw.get("video_summary")),
            "prompt": _to_str(raw.get("prompt")),
            "detailed_prompt": _to_str(raw.get("detailed_prompt")),
            "keywords": _to_str(raw.get("keywords")),
            "keyword_summary": _to_str(raw.get("keyword_summary")),
            "content_type": _to_str(raw.get("content_type")),
            "target_audience": _to_str(raw.get("target_audience")),
            "sentiment": _to_str(raw.get("sentiment")),
            "key_quotes": key_quotes_str,
            "action_items": action_items,
            "difficulty_level": _to_str(raw.get("difficulty_level")),
        }

    def analyze_transcript(self, transcript: str, ui_lang: str = "tr") -> dict:
        try:
            max_chars = int(os.getenv("MAX_TRANSCRIPT_CHARS", "8000"))
            trimmed = transcript[:max_chars]
            system_prompt = _build_prompt(_SINGLE_VIDEO_SYSTEM_PROMPT, ui_lang)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Video Transkripti:\n\n{trimmed}"},
                ],
                temperature=0.4,
            )

            content = response.choices[0].message.content
            raw = self._parse_json_response(content)
            return self._normalize_result(raw)

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise Exception(f"AI analizi sırasında hata: {str(e)}")

    def analyze_playlist_combined(self, transcripts: list[dict], ui_lang: str = "tr") -> dict:
        try:
            max_per_video = 3000
            parts = []
            for i, t in enumerate(transcripts, 1):
                text = t["text"][:max_per_video]
                parts.append(f"--- Video {i}: {t['title']} ---\n{text}")

            combined = "\n\n".join(parts)[:15000]
            system_prompt = _build_prompt(_PLAYLIST_SYSTEM_PROMPT, ui_lang)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Oynatma Listesi Transkriptleri:\n\n{combined}"},
                ],
                temperature=0.4,
            )

            content = response.choices[0].message.content
            raw = self._parse_json_response(content)
            return self._normalize_result(raw)

        except Exception as e:
            logger.error(f"Playlist AI analysis error: {e}")
            raise Exception(f"Playlist AI analizi sırasında hata: {str(e)}")
