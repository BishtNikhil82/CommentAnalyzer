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

class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int