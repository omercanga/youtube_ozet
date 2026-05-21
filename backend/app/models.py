from sqlalchemy import Column, Integer, String, Text, DateTime, Date, UniqueConstraint
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


class RateLimit(Base):
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), nullable=False)
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint("ip_address", "date", name="uq_ip_date"),)
