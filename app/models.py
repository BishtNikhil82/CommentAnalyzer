from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class SearchFilters(BaseModel):
    upload_date: Optional[Literal["hour", "today", "week", "month", "year"]] = None
    duration: Optional[Literal["short", "medium", "long"]] = None
    sort_by: Optional[Literal["relevance", "date", "viewCount", "rating"]] = "relevance"
    language: Optional[str] = None

class Comment(BaseModel):
    text: str
    sentiment: Literal["positive", "neutral", "negative"]
    author: str
    likeCount: int
    replyCount: Optional[int] = 0
    textOriginal: Optional[str] = None
    publishedAt: Optional[str] = None

class SentimentSummary(BaseModel):
    positive: float = Field(..., ge=0, le=1)
    neutral: float = Field(..., ge=0, le=1)
    negative: float = Field(..., ge=0, le=1)

class VideoAnalysis(BaseModel):
    videoId: str
    title: str
    channelName: str
    thumbnailUrl: str
    publishedAt: str
    viewCount: int
    commentCount: int
    sentimentSummary: SentimentSummary
    topKeywords: List[str]
    pros: List[str]
    cons: List[str]
    nextTopicIdeas: List[str]
    comments: List[Comment]

class BatchProcessingStatus(BaseModel):
    current_video: int
    total_videos: int
    video_id: str
    video_title: str
    status: Literal["fetching_comments", "analyzing_comments", "completed", "error"]
    comments_fetched: Optional[int] = None
    error_message: Optional[str] = None
    
class BatchAnalysisResponse(BaseModel):
    videos: List[VideoAnalysis]
    total_processed: int
    successful_analyses: int
    failed_analyses: int
    processing_time_seconds: float

class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int