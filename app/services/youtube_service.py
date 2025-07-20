import httpx
import logging
from typing import List, Dict, Optional
from fastapi import HTTPException
from app.models import SearchFilters

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_videos(
        self,
        query: str,
        max_results: int,
        api_key: str,
        filters: Optional[SearchFilters] = None
    ) -> List[Dict]:
        """Search for YouTube videos using the YouTube Data API v3"""
        try:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": api_key
            }
            
            # Apply filters if provided
            if filters:
                if filters.upload_date:
                    params["publishedAfter"] = self._get_date_filter(filters.upload_date)
                if filters.duration:
                    params["videoDuration"] = filters.duration
                if filters.sort_by:
                    params["order"] = filters.sort_by
                if filters.language:
                    params["relevanceLanguage"] = filters.language
            
            response = await self.client.get(f"{self.base_url}/search", params=params)
            
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail="Invalid or expired YouTube API key")
            elif response.status_code == 429:
                raise HTTPException(status_code=429, detail="YouTube API quota exceeded")
            elif response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="YouTube API error")
            
            data = response.json()
            videos = []
            
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # Get additional video details
                video_details = await self._get_video_details(video_id, api_key)
                
                video_data = {
                    "videoId": video_id,
                    "title": snippet["title"],
                    "channelName": snippet["channelTitle"],
                    "thumbnailUrl": snippet["thumbnails"]["medium"]["url"],
                    "publishedAt": snippet["publishedAt"],
                    "viewCount": video_details.get("viewCount", 0),
                    "duration": video_details.get("duration", "")
                }
                videos.append(video_data)
            
            return videos
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to search videos: {str(e)}")
    
    async def _get_video_details(self, video_id: str, api_key: str) -> Dict:
        """Get additional video details like view count and duration"""
        try:
            params = {
                "part": "statistics,contentDetails",
                "id": video_id,
                "key": api_key
            }
            
            response = await self.client.get(f"{self.base_url}/videos", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    item = data["items"][0]
                    return {
                        "viewCount": int(item.get("statistics", {}).get("viewCount", 0)),
                        "duration": item.get("contentDetails", {}).get("duration", "")
                    }
            
            return {"viewCount": 0, "duration": ""}
            
        except Exception as e:
            logger.error(f"Error getting video details: {str(e)}")
            return {"viewCount": 0, "duration": ""}
    
    async def get_video_comments(
        self,
        video_id: str,
        api_key: str,
        max_results: int = 100
    ) -> List[Dict]:
        """Get comments for a specific video"""
        try:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": max_results,
                "order": "relevance",
                "textFormat": "plainText",
                "key": api_key
            }
            
            response = await self.client.get(f"{self.base_url}/commentThreads", params=params)
            
            if response.status_code == 403:
                # Comments might be disabled for this video
                logger.warning(f"Comments disabled or restricted for video {video_id}")
                return []
            elif response.status_code != 200:
                logger.error(f"Error fetching comments for video {video_id}: {response.status_code}")
                return []
            
            data = response.json()
            comments = []
            
            for item in data.get("items", []):
                comment_data = item["snippet"]["topLevelComment"]["snippet"]
                
                comment = {
                    "text": comment_data["textDisplay"],
                    "author": comment_data["authorDisplayName"],
                    "likeCount": comment_data.get("likeCount", 0),
                    "publishedAt": comment_data["publishedAt"]
                }
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments for video {video_id}: {str(e)}")
            return []
    
    def _get_date_filter(self, upload_date: str) -> str:
        """Convert upload_date filter to RFC 3339 formatted date"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        if upload_date == "hour":
            date = now - timedelta(hours=1)
        elif upload_date == "today":
            date = now - timedelta(days=1)
        elif upload_date == "week":
            date = now - timedelta(weeks=1)
        elif upload_date == "month":
            date = now - timedelta(days=30)
        elif upload_date == "year":
            date = now - timedelta(days=365)
        else:
            return ""
        
        return date.isoformat() + "Z"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()