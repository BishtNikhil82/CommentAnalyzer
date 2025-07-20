from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
import logging
from app.models import VideoAnalysis, SearchFilters
from app.services.youtube_service import YouTubeService
from app.services.analysis_service import AnalysisService
from app.utils.rate_limiter import RateLimiter
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Comment Analyzer",
    description="Analyze YouTube comments for content insights and sentiment analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
youtube_service = YouTubeService()
analysis_service = AnalysisService()
rate_limiter = RateLimiter()

@app.get("/analyze-youtube", response_model=List[VideoAnalysis])
async def analyze_youtube_comments(
    query: str = Query(..., description="YouTube search keyword/phrase"),
    video_count: int = Query(..., ge=1, le=50, description="Number of videos to analyze (1-50)"),
    api_key: str = Query(..., description="YouTube Data API v3 access key"),
    filters: Optional[str] = Query(None, description="JSON string with search filters"),
    _: None = Depends(rate_limiter.check_rate_limit)
):
    """
    Analyze YouTube comments for content insights and sentiment analysis.
    
    This endpoint searches for YouTube videos, extracts comments, and performs
    detailed sentiment and content analysis including keyword extraction,
    pros/cons identification, and next topic suggestions.
    """
    try:
        logger.info(f"Starting analysis for query: {query}, video_count: {video_count}")
        
        # Parse filters if provided
        search_filters = None
        if filters:
            try:
                filter_dict = json.loads(filters)
                search_filters = SearchFilters(**filter_dict)
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid filters JSON: {str(e)}")
        
        # Search for videos
        videos = await youtube_service.search_videos(
            query=query,
            max_results=video_count,
            api_key=api_key,
            filters=search_filters
        )
        
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for the given query")
        
        # Analyze each video
        results = []
        for video in videos:
            try:
                # Get comments for the video
                comments = await youtube_service.get_video_comments(
                    video_id=video["videoId"],
                    api_key=api_key,
                    max_results=100
                )
                
                # Perform analysis
                analysis_result = await analysis_service.analyze_video_comments(
                    video_data=video,
                    comments=comments
                )
                
                results.append(analysis_result)
                logger.info(f"Completed analysis for video: {video['title']}")
                
            except Exception as e:
                logger.error(f"Error analyzing video {video['videoId']}: {str(e)}")
                # Continue with other videos even if one fails
                continue
        
        if not results:
            raise HTTPException(status_code=500, detail="Failed to analyze any videos")
        
        logger.info(f"Successfully analyzed {len(results)} videos")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_youtube_comments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "YouTube Comment Analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )