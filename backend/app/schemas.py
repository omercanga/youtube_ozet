from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# --- Single Video ---

class AnalyzeRequest(BaseModel):
    video_url: str


class ManualAnalyzeRequest(BaseModel):
    title: str
    transcript_text: str
    source_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    id: int
    video_url: str
    video_id: str
    video_title: Optional[str] = None
    summary: str
    video_summary: Optional[str] = None
    generated_prompt: str
    detailed_prompt: Optional[str] = None
    keywords: Optional[str] = None
    content_type: Optional[str] = None
    target_audience: Optional[str] = None
    sentiment: Optional[str] = None
    key_quotes: Optional[str] = None
    action_items: Optional[str] = None
    difficulty_level: Optional[str] = None
    one_liner: Optional[str] = None
    keyword_summary: Optional[str] = None
    playlist_id: Optional[str] = None
    playlist_title: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    id: int
    video_url: str
    video_title: Optional[str] = None
    summary: str
    video_summary: Optional[str] = None
    keywords: Optional[str] = None
    content_type: Optional[str] = None
    playlist_id: Optional[str] = None
    playlist_title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryDetail(BaseModel):
    id: int
    video_url: str
    video_id: str
    video_title: Optional[str] = None
    transcript_text: str
    summary: str
    video_summary: Optional[str] = None
    generated_prompt: str
    detailed_prompt: Optional[str] = None
    keywords: Optional[str] = None
    content_type: Optional[str] = None
    target_audience: Optional[str] = None
    sentiment: Optional[str] = None
    key_quotes: Optional[str] = None
    action_items: Optional[str] = None
    difficulty_level: Optional[str] = None
    one_liner: Optional[str] = None
    keyword_summary: Optional[str] = None
    playlist_id: Optional[str] = None
    playlist_title: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Playlist ---

class PlaylistVideoItem(BaseModel):
    video_id: str
    title: str
    duration: Optional[str] = None
    thumbnail: Optional[str] = None


class PlaylistInfoResponse(BaseModel):
    playlist_id: str
    playlist_title: Optional[str] = None
    video_count: int
    videos: List[PlaylistVideoItem]


class PlaylistAnalyzeRequest(BaseModel):
    playlist_url: str
    video_ids: List[str]
    mode: str = "individual"  # "individual" or "combined"
