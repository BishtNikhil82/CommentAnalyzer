import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class YouTubeAPIParser:
    """Parser for YouTube API search responses"""
    
    def __init__(self):
        pass
    
    def parse_search_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse YouTube API searchListResponse and extract structured video information
        
        Args:
            api_response: YouTube API searchListResponse JSON object
            
        Returns:
            Dictionary containing parsed video data and metadata
        """
        try:
            # Extract metadata
            page_info = api_response.get("pageInfo", {})
            total_results = page_info.get("totalResults", 0)
            results_per_page = page_info.get("resultsPerPage", 0)
            
            # Parse video items
            items = api_response.get("items", [])
            parsed_videos = []
            
            for index, item in enumerate(items, 1):
                video_data = self._parse_video_item(item, index)
                if video_data:
                    parsed_videos.append(video_data)
            
            return {
                "metadata": {
                    "total_results": total_results,
                    "results_per_page": results_per_page,
                    "videos_parsed": len(parsed_videos),
                    "next_page_token": api_response.get("nextPageToken"),
                    "region_code": api_response.get("regionCode")
                },
                "videos": parsed_videos
            }
            
        except Exception as e:
            return {
                "error": f"Failed to parse API response: {str(e)}",
                "metadata": {},
                "videos": []
            }
    
    def _parse_video_item(self, item: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Parse individual video item from API response"""
        try:
            # Extract video ID
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                return None
            
            snippet = item.get("snippet", {})
            
            # Extract basic information
            title = snippet.get("title", "N/A")
            channel_name = snippet.get("channelTitle", "N/A")
            channel_id = snippet.get("channelId", "N/A")
            
            # Handle description
            description = snippet.get("description", "")
            if not description:
                description = "No description"
            elif len(description) > 100:
                description = description[:100] + "..."
            
            # Format publish date
            published_at = snippet.get("publishedAt", "")
            formatted_date = self._format_date(published_at)
            
            # Extract thumbnail URL
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("medium", {}).get("url", "N/A")
            
            # Construct video URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            return {
                "index": index,
                "video_id": video_id,
                "title": title,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "description": description,
                "published_at": formatted_date,
                "thumbnail_url": thumbnail_url,
                "video_url": video_url,
                "raw_publish_date": published_at
            }
            
        except Exception as e:
            return {
                "index": index,
                "error": f"Failed to parse video item: {str(e)}",
                "video_id": "N/A",
                "title": "N/A",
                "channel_name": "N/A",
                "channel_id": "N/A",
                "description": "N/A",
                "published_at": "N/A",
                "thumbnail_url": "N/A",
                "video_url": "N/A"
            }
    
    def _format_date(self, date_string: str) -> str:
        """Format ISO date string to readable format"""
        try:
            if not date_string:
                return "N/A"
            
            # Parse ISO format date
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p UTC")
            
        except Exception:
            return date_string if date_string else "N/A"
    
    def format_output(self, parsed_data: Dict[str, Any]) -> str:
        """Format parsed data into readable text output"""
        if "error" in parsed_data:
            return f"Error: {parsed_data['error']}"
        
        metadata = parsed_data.get("metadata", {})
        videos = parsed_data.get("videos", [])
        
        # Build formatted output
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("YOUTUBE API SEARCH RESULTS PARSER")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        # Metadata section
        output_lines.append(f"Total Results: {metadata.get('total_results', 'N/A'):,}")
        output_lines.append(f"Results Per Page: {metadata.get('results_per_page', 'N/A')}")
        output_lines.append(f"Videos Parsed: {metadata.get('videos_parsed', 'N/A')}")
        if metadata.get('region_code'):
            output_lines.append(f"Region Code: {metadata['region_code']}")
        if metadata.get('next_page_token'):
            output_lines.append(f"Next Page Token: {metadata['next_page_token']}")
        output_lines.append("")
        output_lines.append("-" * 80)
        output_lines.append("")
        
        # Videos section
        for video in videos:
            if "error" in video:
                output_lines.append(f"Video {video['index']}: ERROR - {video['error']}")
                output_lines.append("")
                continue
            
            output_lines.append(f"Video {video['index']}:")
            output_lines.append(f"- ID: {video['video_id']}")
            output_lines.append(f"- Title: {video['title']}")
            output_lines.append(f"- Channel: {video['channel_name']}")
            output_lines.append(f"- Channel ID: {video['channel_id']}")
            output_lines.append(f"- Published: {video['published_at']}")
            output_lines.append(f"- Description: {video['description']}")
            output_lines.append(f"- Thumbnail: {video['thumbnail_url']}")
            output_lines.append(f"- Watch URL: {video['video_url']}")
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def parse_and_format(self, api_response: Dict[str, Any]) -> str:
        """Parse API response and return formatted output"""
        parsed_data = self.parse_search_response(api_response)
        return self.format_output(parsed_data)


# Convenience function for direct usage
def parse_youtube_response(api_response: Dict[str, Any]) -> str:
    """
    Parse YouTube API response and return formatted output
    
    Args:
        api_response: YouTube API searchListResponse JSON object
        
    Returns:
        Formatted string with parsed video information
    """
    parser = YouTubeAPIParser()
    return parser.parse_and_format(api_response)


# Example usage and test with provided data
if __name__ == "__main__":
    # Sample API response for testing
    sample_response = {
        "kind": "youtube#searchListResponse",
        "etag": "CoKwf2qRIHXgNT4srxfprFe_pJs",
        "nextPageToken": "CAoQAA",
        "regionCode": "IN",
        "pageInfo": {
            "totalResults": 1000000,
            "resultsPerPage": 10
        },
        "items": [
            {
                "kind": "youtube#searchResult",
                "etag": "9BgZuB8XmQJ_I42ZZ2OJLHuwJCs",
                "id": {
                    "kind": "youtube#video",
                    "videoId": "7_ODjBCJ4QM"
                },
                "snippet": {
                    "publishedAt": "2025-07-19T11:34:56Z",
                    "channelId": "UC6JEz6BKg7hX7idKecN7QYA",
                    "title": "How the Conspiracy to Kill Rajiv Gandhi Was Planned ft. Anirudhya | The Hunt  | Jist",
                    "description": "In this gripping episode of the Jist Podcast, journalist Mukul speaks with veteran investigative journalist Anirudhya Mitra, the ...",
                    "thumbnails": {
                        "default": {
                            "url": "https://i.ytimg.com/vi/7_ODjBCJ4QM/default.jpg",
                            "width": 120,
                            "height": 90
                        },
                        "medium": {
                            "url": "https://i.ytimg.com/vi/7_ODjBCJ4QM/mqdefault.jpg",
                            "width": 320,
                            "height": 180
                        },
                        "high": {
                            "url": "https://i.ytimg.com/vi/7_ODjBCJ4QM/hqdefault.jpg",
                            "width": 480,
                            "height": 360
                        }
                    },
                    "channelTitle": "Jist",
                    "liveBroadcastContent": "none",
                    "publishTime": "2025-07-19T11:34:56Z"
                }
            },
            {
                "kind": "youtube#searchResult",
                "etag": "tm1q-s9wvUl4TuWf5IJpGHv3hss",
                "id": {
                    "kind": "youtube#video",
                    "videoId": "evQXcu0jeYA"
                },
                "snippet": {
                    "publishedAt": "2025-07-19T04:17:56Z",
                    "channelId": "UCVKJPyNj5PK41sCTw1Vp7Kw",
                    "title": "Lucky Bisht reveals RAW's Message  to Rajiv Gandhi #shorts #viralvideo #luckybisht",
                    "description": "",
                    "thumbnails": {
                        "default": {
                            "url": "https://i.ytimg.com/vi/evQXcu0jeYA/default.jpg",
                            "width": 120,
                            "height": 90
                        },
                        "medium": {
                            "url": "https://i.ytimg.com/vi/evQXcu0jeYA/mqdefault.jpg",
                            "width": 320,
                            "height": 180
                        },
                        "high": {
                            "url": "https://i.ytimg.com/vi/evQXcu0jeYA/hqdefault.jpg",
                            "width": 480,
                            "height": 360
                        }
                    },
                    "channelTitle": "Hindi Rush",
                    "liveBroadcastContent": "none",
                    "publishTime": "2025-07-19T04:17:56Z"
                }
            }
        ]
    }
    
    # Test the parser
    result = parse_youtube_response(sample_response)
    print(result)