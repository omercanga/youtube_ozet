from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..models import VideoAnalysis
from ..schemas import (
    AnalyzeRequest,
    ManualAnalyzeRequest,
    AnalyzeResponse,
    HistoryItem,
    HistoryDetail,
    PlaylistInfoResponse,
    PlaylistVideoItem,
    PlaylistAnalyzeRequest,
)
from ..services.youtube_service import YouTubeService
from ..services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

youtube_service = YouTubeService()

# Lazy-initialized AI service
_openai_service = None


def get_openai_service():
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


# --- Single Video Analysis ---


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_video(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze a single YouTube video and save results."""
    try:
        # Check if this is a playlist URL (warn the user)
        if youtube_service.is_playlist_url(request.video_url):
            # Extract video_id anyway (watch?v=...&list=... has both)
            video_id = youtube_service.extract_video_id(request.video_url)
            if not video_id:
                raise HTTPException(
                    status_code=400,
                    detail="Bu bir oynatma listesi URL'si. Lütfen 'Oynatma Listesi' sekmesini kullanın veya tek bir video URL'si girin.",
                )
        else:
            video_id = youtube_service.extract_video_id(request.video_url)

        if not video_id:
            raise HTTPException(status_code=400, detail="Geçersiz YouTube URL'si")

        # Get transcript
        transcript_text, language = youtube_service.get_transcript(video_id)

        # Get video info (real title via oEmbed)
        video_info = youtube_service.get_video_info(video_id)

        # Analyze with AI
        analysis = get_openai_service().analyze_transcript(transcript_text)

        # Save to database
        db_analysis = VideoAnalysis(
            video_url=request.video_url,
            video_id=video_id,
            video_title=video_info.get("title"),
            transcript_text=transcript_text,
            summary=analysis["summary"],
            video_summary=analysis.get("video_summary"),
            generated_prompt=analysis["prompt"],
            detailed_prompt=analysis.get("detailed_prompt"),
            keywords=analysis.get("keywords"),
            content_type=analysis.get("content_type"),
            target_audience=analysis.get("target_audience"),
            sentiment=analysis.get("sentiment"),
            key_quotes=analysis.get("key_quotes"),
            action_items=analysis.get("action_items"),
            difficulty_level=analysis.get("difficulty_level"),
            one_liner=analysis.get("one_liner"),
            keyword_summary=analysis.get("keyword_summary"),
            language=language,
        )

        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        return db_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Manual Transcript Analysis ---


@router.post("/analyze-manual", response_model=AnalyzeResponse)
async def analyze_manual(request: ManualAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze manually provided transcript and save results."""
    try:
        if len(request.transcript_text.strip()) < 50:
            raise HTTPException(
                status_code=400, detail="Transkript çok kısa (minimum 50 karakter)"
            )

        analysis = get_openai_service().analyze_transcript(request.transcript_text)

        db_analysis = VideoAnalysis(
            video_url=request.source_url or "Manuel Giriş",
            video_id="manual",
            video_title=request.title,
            transcript_text=request.transcript_text,
            summary=analysis["summary"],
            video_summary=analysis.get("video_summary"),
            generated_prompt=analysis["prompt"],
            detailed_prompt=analysis.get("detailed_prompt"),
            keywords=analysis.get("keywords"),
            content_type=analysis.get("content_type"),
            target_audience=analysis.get("target_audience"),
            sentiment=analysis.get("sentiment"),
            key_quotes=analysis.get("key_quotes"),
            action_items=analysis.get("action_items"),
            difficulty_level=analysis.get("difficulty_level"),
            one_liner=analysis.get("one_liner"),
            keyword_summary=analysis.get("keyword_summary"),
            language="unknown",
        )

        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        return db_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Playlist ---


@router.get("/playlist/info", response_model=PlaylistInfoResponse)
async def get_playlist_info(url: str = Query(..., description="YouTube playlist URL")):
    """Get list of videos in a playlist."""
    try:
        playlist_id = youtube_service.extract_playlist_id(url)
        if not playlist_id:
            raise HTTPException(
                status_code=400, detail="Geçersiz oynatma listesi URL'si"
            )

        videos = youtube_service.get_playlist_videos(playlist_id)
        playlist_title = youtube_service.get_playlist_title(playlist_id)

        return PlaylistInfoResponse(
            playlist_id=playlist_id,
            playlist_title=playlist_title,
            video_count=len(videos),
            videos=[
                PlaylistVideoItem(
                    video_id=v["video_id"],
                    title=v["title"],
                    duration=v.get("duration"),
                    thumbnail=v.get("thumbnail"),
                )
                for v in videos
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlist/analyze", response_model=List[AnalyzeResponse])
async def analyze_playlist(
    request: PlaylistAnalyzeRequest, db: Session = Depends(get_db)
):
    """Analyze selected videos from a playlist (individual or combined mode)."""
    try:
        playlist_id = youtube_service.extract_playlist_id(request.playlist_url)
        if not playlist_id:
            raise HTTPException(
                status_code=400, detail="Geçersiz oynatma listesi URL'si"
            )

        playlist_title = youtube_service.get_playlist_title(playlist_id)

        if not request.video_ids:
            raise HTTPException(
                status_code=400, detail="En az bir video seçmelisiniz"
            )

        # Limit to prevent abuse
        max_videos = 15
        video_ids = request.video_ids[:max_videos]

        if request.mode == "combined":
            # --- Combined mode: merge transcripts, single analysis ---
            transcripts = []
            for vid in video_ids:
                try:
                    text, lang = youtube_service.get_transcript(vid)
                    info = youtube_service.get_video_info(vid)
                    transcripts.append({"title": info["title"], "text": text, "video_id": vid})
                except Exception as e:
                    logger.warning(f"Skipping video {vid}: {e}")
                    continue

            if not transcripts:
                raise HTTPException(
                    status_code=400,
                    detail="Seçilen videoların hiçbirinden transkript alınamadı",
                )

            analysis = get_openai_service().analyze_playlist_combined(transcripts)
            combined_transcript = "\n\n".join(
                [f"[{t['title']}]\n{t['text']}" for t in transcripts]
            )
            video_titles = ", ".join([t["title"] for t in transcripts])

            db_analysis = VideoAnalysis(
                video_url=request.playlist_url,
                video_id=",".join([t["video_id"] for t in transcripts]),
                video_title=f"Playlist: {playlist_title} ({len(transcripts)} video)",
                transcript_text=combined_transcript[:50000],
                summary=analysis["summary"],
                video_summary=analysis.get("video_summary"),
                generated_prompt=analysis["prompt"],
                detailed_prompt=analysis.get("detailed_prompt"),
                keywords=analysis.get("keywords"),
                content_type=analysis.get("content_type"),
                target_audience=analysis.get("target_audience"),
                sentiment=analysis.get("sentiment"),
                key_quotes=analysis.get("key_quotes"),
                action_items=analysis.get("action_items"),
                difficulty_level=analysis.get("difficulty_level"),
                one_liner=analysis.get("one_liner"),
                keyword_summary=analysis.get("keyword_summary"),
                playlist_id=playlist_id,
                playlist_title=playlist_title,
                language="mixed",
            )
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)

            return [db_analysis]

        else:
            # --- Individual mode: analyze each video separately ---
            results = []
            for vid in video_ids:
                try:
                    transcript_text, language = youtube_service.get_transcript(vid)
                    video_info = youtube_service.get_video_info(vid)
                    analysis = get_openai_service().analyze_transcript(transcript_text)

                    db_analysis = VideoAnalysis(
                        video_url=f"https://www.youtube.com/watch?v={vid}",
                        video_id=vid,
                        video_title=video_info.get("title"),
                        transcript_text=transcript_text,
                        summary=analysis["summary"],
                        video_summary=analysis.get("video_summary"),
                        generated_prompt=analysis["prompt"],
                        detailed_prompt=analysis.get("detailed_prompt"),
                        keywords=analysis.get("keywords"),
                        content_type=analysis.get("content_type"),
                        target_audience=analysis.get("target_audience"),
                        sentiment=analysis.get("sentiment"),
                        key_quotes=analysis.get("key_quotes"),
                        action_items=analysis.get("action_items"),
                        difficulty_level=analysis.get("difficulty_level"),
                        one_liner=analysis.get("one_liner"),
                        keyword_summary=analysis.get("keyword_summary"),
                        playlist_id=playlist_id,
                        playlist_title=playlist_title,
                        language=language,
                    )
                    db.add(db_analysis)
                    db.commit()
                    db.refresh(db_analysis)
                    results.append(db_analysis)

                except Exception as e:
                    logger.warning(f"Failed to analyze video {vid}: {e}")
                    continue

            if not results:
                raise HTTPException(
                    status_code=400,
                    detail="Seçilen videoların hiçbiri analiz edilemedi",
                )

            return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- History ---


@router.get("/history", response_model=List[HistoryItem])
async def get_history(db: Session = Depends(get_db)):
    """Get all analysis history."""
    analyses = db.query(VideoAnalysis).order_by(VideoAnalysis.created_at.desc()).all()
    return analyses


@router.get("/history/{analysis_id}", response_model=HistoryDetail)
async def get_analysis_detail(analysis_id: int, db: Session = Depends(get_db)):
    """Get detailed analysis by ID."""
    analysis = (
        db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")
    return analysis


@router.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete an analysis."""
    analysis = (
        db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")

    db.delete(analysis)
    db.commit()
    return {"message": "Analiz silindi"}
