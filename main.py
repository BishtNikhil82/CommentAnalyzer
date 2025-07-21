from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from youtube_api import search_youtube_videos, fetch_top_comments
from llm_analyzer import analyze_video_comments
from typing import List, Optional
import logging

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

@app.get("/analyze-youtube", response_model=List[AnalyzeYouTubeResponse])
def analyze_youtube(
    query: str = Query(..., description="YouTube search keyword/phrase"),
    maxResults: int = Query(5, ge=1, le=50, description="Number of videos to analyze (1-50)"),
    order: str = Query("relevance", description="Order of search results"),
    regionCode: Optional[str] = Query(None, description="Region code (e.g., IN)"),
    topic: Optional[str] = Query(None, description="Topic to search (optional)")
):
    logger.info(f"/analyze-youtube called with query='{query}', maxResults={maxResults}, order='{order}', regionCode='{regionCode}', topic='{topic}'")
    try:
        videos = search_youtube_videos(query, maxResults, order, regionCode)
        logger.info(f"YouTube search returned {len(videos)} videos.")
        if not videos:
            logger.error("No videos found for the given query.")
            raise HTTPException(status_code=404, detail="No videos found for the given query")
        results = []
        for idx, video in enumerate(videos):
            logger.info(f"Processing video {idx+1}/{len(videos)}: {video['video_title']} (ID: {video['video_id']})")
            comments = fetch_top_comments(video['video_id'])
            analysis = analyze_video_comments(video, comments)
            results.append(analysis)
        logger.info(f"Analysis complete for {len(results)} videos.")
        return results
    except Exception as e:
        logger.exception(f"Error in /analyze-youtube: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 