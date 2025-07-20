from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import time
import asyncio
import logging
from app.models import VideoAnalysis, SearchFilters, BatchAnalysisResponse, BatchProcessingStatus
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

@app.get("/analyze-youtube", response_model=BatchAnalysisResponse)
async def analyze_youtube_comments(
    query: str = Query(..., description="YouTube search keyword/phrase"),
    video_count: int = Query(..., ge=1, le=50, description="Number of videos to analyze (1-50)"),
    api_key: str = Query(..., description="YouTube Data API v3 access key"),
    filters: Optional[str] = Query(None, description="JSON string with search filters"),
    batch_mode: bool = Query(True, description="Enable sequential batch processing"),
    _: None = Depends(rate_limiter.check_rate_limit)
):
    """
    Analyze YouTube comments for content insights and sentiment analysis with batch processing.
    
    This endpoint searches for YouTube videos, extracts exactly 100 comments per video
    using pagination, and performs detailed sentiment and content analysis including 
    keyword extraction, pros/cons identification, and next topic suggestions.
    
    Videos are processed sequentially to respect API rate limits and provide
    structured batch processing with progress tracking.
    """
    try:
        start_time = time.time()
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
        
        if batch_mode:
            # Use sequential batch processing
            results = await analysis_service.analyze_videos_batch(
                videos=videos,
                youtube_service=youtube_service,
                api_key=api_key
            )
        else:
            # Legacy concurrent processing (kept for compatibility)
            results = []
            for video in videos:
                try:
                    comments = await youtube_service.get_video_comments(
                        video_id=video["videoId"],
                        api_key=api_key,
                        max_results=100
                    )
                    
                    analysis_result = await analysis_service.analyze_video_comments(
                        video_data=video,
                        comments=comments
                    )
                    
                    results.append(analysis_result)
                    logger.info(f"Completed analysis for video: {video['title']}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing video {video['videoId']}: {str(e)}")
                    continue
        
        if not results:
            raise HTTPException(status_code=500, detail="Failed to analyze any videos")
        
        processing_time = time.time() - start_time
        successful_analyses = len([r for r in results if r.commentCount > 0 or len(r.topKeywords) > 0])
        failed_analyses = len(results) - successful_analyses
        
        logger.info(f"Successfully analyzed {len(results)} videos")
        
        return BatchAnalysisResponse(
            videos=results,
            total_processed=len(results),
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_youtube_comments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/analyze-youtube-stream")
async def analyze_youtube_comments_stream(
    query: str = Query(..., description="YouTube search keyword/phrase"),
    video_count: int = Query(..., ge=1, le=50, description="Number of videos to analyze (1-50)"),
    api_key: str = Query(..., description="YouTube Data API v3 access key"),
    filters: Optional[str] = Query(None, description="JSON string with search filters"),
    _: None = Depends(rate_limiter.check_rate_limit)
):
    """
    Stream YouTube comment analysis results with real-time progress updates.
    
    This endpoint provides real-time streaming of analysis progress and results
    as each video is processed sequentially.
    """
    async def generate_stream():
        try:
            # Parse filters if provided
            search_filters = None
            if filters:
                try:
                    filter_dict = json.loads(filters)
                    search_filters = SearchFilters(**filter_dict)
                except (json.JSONDecodeError, ValueError) as e:
                    yield f"data: {json.dumps({'error': f'Invalid filters JSON: {str(e)}'})}\n\n"
                    return
            
            # Search for videos
            videos = await youtube_service.search_videos(
                query=query,
                max_results=video_count,
                api_key=api_key,
                filters=search_filters
            )
            
            if not videos:
                yield f"data: {json.dumps({'error': 'No videos found for the given query'})}\n\n"
                return
            
            # Stream progress updates
            async def progress_callback(status: BatchProcessingStatus):
                yield f"data: {json.dumps(status.dict())}\n\n"
            
            # Process videos with streaming updates
            results = await analysis_service.analyze_videos_batch(
                videos=videos,
                youtube_service=youtube_service,
                api_key=api_key,
                progress_callback=progress_callback
            )
            
            # Send final results
            final_response = BatchAnalysisResponse(
                videos=results,
                total_processed=len(results),
                successful_analyses=len([r for r in results if r.commentCount > 0]),
                failed_analyses=len(results) - len([r for r in results if r.commentCount > 0]),
                processing_time_seconds=0  # Will be calculated on client side
            )
            yield f"data: {json.dumps({'final_results': final_response.dict()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Stream error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

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