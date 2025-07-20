import pytest
from unittest.mock import AsyncMock, patch
from app.services.youtube_service import YouTubeService
from app.models import SearchFilters

class TestYouTubeService:
    def setup_method(self):
        self.youtube_service = YouTubeService()
    
    @pytest.mark.asyncio
    async def test_search_videos_success(self):
        """Test successful video search"""
        mock_response = {
            "items": [
                {
                    "id": {"videoId": "test123"},
                    "snippet": {
                        "title": "Test Video",
                        "channelTitle": "Test Channel",
                        "thumbnails": {"medium": {"url": "http://test.jpg"}},
                        "publishedAt": "2023-01-01T00:00:00Z"
                    }
                }
            ]
        }
        
        with patch.object(self.youtube_service.client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            # Mock the video details call
            with patch.object(self.youtube_service, '_get_video_details') as mock_details:
                mock_details.return_value = {"viewCount": 1000, "duration": "PT5M"}
                
                videos = await self.youtube_service.search_videos(
                    query="test",
                    max_results=1,
                    api_key="test_key"
                )
                
                assert len(videos) == 1
                assert videos[0]["videoId"] == "test123"
                assert videos[0]["title"] == "Test Video"
    
    @pytest.mark.asyncio
    async def test_get_video_comments_success(self):
        """Test successful comment retrieval"""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "textDisplay": "Great video!",
                                "authorDisplayName": "Test User",
                                "likeCount": 5,
                                "publishedAt": "2023-01-01T00:00:00Z"
                            }
                        }
                    }
                }
            ]
        }
        
        with patch.object(self.youtube_service.client, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            comments = await self.youtube_service.get_video_comments(
                video_id="test123",
                api_key="test_key"
            )
            
            assert len(comments) == 1
            assert comments[0]["text"] == "Great video!"
            assert comments[0]["author"] == "Test User"
    
    def test_get_date_filter(self):
        """Test date filter conversion"""
        date_filter = self.youtube_service._get_date_filter("week")
        assert date_filter.endswith("Z")
        assert "T" in date_filter  # ISO format check