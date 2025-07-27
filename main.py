from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from youtube_api import search_youtube_videos, fetch_top_comments
from llm_analyzer import analyze_video_comments
from typing import List, Optional
import logging
from db.supabase_client import insert_job_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Comment Analyzer (LLM Only)")

class AnalyzeYouTubeResponse(BaseModel):
    video_id: str
    video_title: str
    channelTitle: str
    thumbnail_url: str
    publishTime: str
    pros: str
    cons: str
    next_hot_topic: str
    reason: Optional[str] = None
    comments_fetched: Optional[int] = None
    comments_sanitized: Optional[int] = None

from fastapi import Header, HTTPException, Query
from typing import Optional, List
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from fastapi.responses import StreamingResponse
import json

@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.get("/analyze-youtube")
def analyze_youtube(
    query: str = Query(..., description="YouTube search keyword/phrase"),
    maxResults: int = Query(5, ge=1, le=50, description="Number of videos to analyze (1-50)"),
    order: str = Query("relevance", description="Order of search results"),
    regionCode: Optional[str] = Query(None, description="Region code (e.g., IN)"),
    topic: Optional[str] = Query(None, description="Topic to search (optional)"),
    job_id: int = Query(..., description="Job ID for tracking (BIGINT)"),
    authorization: Optional[str] = Header(None)
    ):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    youtube_token = authorization.split(" ")[1]
    logger.info(f"Received OAuth token: {youtube_token[:10]}...")

    def event_stream():
        try:
            videos = search_youtube_videos(query, maxResults, order, regionCode, youtube_token)
            logger.info(f"YouTube search returned {len(videos)} videos.")
            if not videos:
                yield f"data: {json.dumps({'error': 'No videos found'})}\n\n"
                return

            for idx, video in enumerate(videos):
                logger.info(f"Processing video {idx+1}/{len(videos)}: {video['video_title']} (ID: {video['video_id']})")
                comments = fetch_top_comments(video['video_id'], 10 ,youtube_token)
                analysis = analyze_video_comments(video, comments)
                # Insert into Supabase
                try:
                    insert_job_result(job_id, video, analysis)
                except Exception as db_exc:
                    logger.error(f"Failed to insert job result for video {video['video_id']}: {db_exc}")
                yield f"data: {json.dumps({'type': 'video', 'data': analysis})}\n\n"

        except Exception as e:
            logger.exception(f"Error in /analyze-youtube: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
