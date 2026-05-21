from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base


class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String(500), nullable=False)
    video_id = Column(String(50), nullable=False, index=True)
    video_title = Column(String(500))
    transcript_text = Column(Text, nullable=False)

    # Core analysis fields
    summary = Column(Text, nullable=False)
    video_summary = Column(Text)
    generated_prompt = Column(Text, nullable=False)
    detailed_prompt = Column(Text)

    # Enriched analysis fields (v2)
    keywords = Column(Text)
    content_type = Column(String(100))
    target_audience = Column(String(200))

    # Deep analysis fields (v3)
    sentiment = Column(String(100))
    key_quotes = Column(Text)
    action_items = Column(Text)
    difficulty_level = Column(String(50))
    one_liner = Column(String(300))
    keyword_summary = Column(Text)        # Each keyword with contextual explanation

    # Playlist tracking
    playlist_id = Column(String(100), index=True)
    playlist_title = Column(String(500))

    # Metadata
    language = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
