#!/usr/bin/env python3
"""
Test script for YouTube API Parser
Run this to see the parser in action with the provided sample data
"""

import json
from app.utils.youtube_parser import parse_youtube_response

# Your provided sample data
sample_api_response = {
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

if __name__ == "__main__":
    print("🔍 Testing YouTube API Parser with provided sample data...\n")
    
    # Parse and display the results
    result = parse_youtube_response(sample_api_response)
    print(result)
    
    print("\n" + "="*80)
    print("✅ Parser test completed successfully!")
    print("="*80)