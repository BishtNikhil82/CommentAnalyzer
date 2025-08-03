import os
import requests
import logging
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _parse_duration(duration_str: str) -> int:
    if not duration_str or not duration_str.startswith('PT'):
        return 0
    duration_str = duration_str[2:]
    total_seconds = 0
    hours_match = re.search(r'(\d+)H', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    minutes_match = re.search(r'(\d+)M', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    seconds_match = re.search(r'(\d+)S', duration_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    return total_seconds

# def search_youtube_videos(query, maxResults=1, order="relevance", regionCode=None, youtube_token=None):
    if not youtube_token:
        logger.error("Missing YouTube OAuth token")
        return []

    headers = {
        "Authorization": f"Bearer {youtube_token}",
        "Accept": "application/json"
    }

    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(50, maxResults * 2),
        "order": order,
        "videoDuration": "medium"
    }
    if regionCode:
        search_params["regionCode"] = regionCode

    logger.info(f"YouTube Search API request: {search_url} params={search_params}")
    search_resp = requests.get(search_url, headers=headers, params=search_params)
    logger.info(f"YouTube Search API response status: {search_resp.status_code}")
    if search_resp.status_code != 200:
        logger.error(f"YouTube API error: {search_resp.text}")
        return []

    video_ids = [item["id"]["videoId"] for item in search_resp.json().get("items", [])]
    if not video_ids:
        return []

    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids)
    }
    videos_resp = requests.get(videos_url, headers=headers, params=videos_params)
    if videos_resp.status_code != 200:
        logger.error(f"YouTube Videos API error: {videos_resp.text}")
        return []

    final_videos = []
    for item in videos_resp.json().get("items", []):
        # duration_seconds = _parse_duration(item.get("contentDetails", {}).get("duration"))
        # if duration_seconds < 300:  # Skip videos less than 5 minutes
        #     continue

        snippet = item["snippet"]
        final_videos.append({
            "video_id": item["id"],
            "video_title": snippet["title"],
            "channelTitle": snippet["channelTitle"],
            "thumbnail_url": snippet["thumbnails"].get("high", snippet["thumbnails"]["default"])['url'],
            "publishTime": snippet.get("publishTime", snippet.get("publishedAt", ""))
        })
        if len(final_videos) >= maxResults:
            break

    logger.info(f"YouTube Search API returned {len(final_videos)} videos after filtering.")
    return final_videos

def search_youtube_videos(query, maxResults=1, order="relevance", regionCode=None, youtube_token=None):
    if not youtube_token:
        logger.error("YouTube API: Missing YouTube OAuth token")
        return []

    headers = {
        "Authorization": f"Bearer {youtube_token}",
        "Accept": "application/json"
    }

    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",  # Ensures only videos are requested
        "maxResults": min(50, maxResults * 2),
        "order": order,
        "videoDuration": "long"
    }

    if regionCode:
        search_params["regionCode"] = regionCode

    logger.info(f"YouTube API: Search request: {search_url} params={search_params}")
    search_resp = requests.get(search_url, headers=headers, params=search_params)
    logger.info(f"YouTube API: Search response status: {search_resp.status_code}")
    
    if search_resp.status_code != 200:
        logger.error(f"YouTube API: Search API error: {search_resp.text}")
        return []

    search_items = search_resp.json().get("items", [])
    
    if not search_items:
        logger.warning(f"YouTube API: No search results found for query: {query}")
        return []

    logger.info(f"YouTube API: Found {len(search_items)} search results for query: {query}")

    # ✅ Safe videoId extraction
    video_ids = [
        item["id"]["videoId"]
        for item in search_items
        if item.get("id", {}).get("kind") == "youtube#video" and "videoId" in item["id"]
    ]

    if not video_ids:
        logger.warning("YouTube API: No valid video IDs found in search results.")
        return []

    logger.info(f"YouTube API: Extracted {len(video_ids)} valid video IDs")

    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids)
    }

    videos_resp = requests.get(videos_url, headers=headers, params=videos_params)
    logger.info(f"YouTube API: Videos response status: {videos_resp.status_code}")
    
    if videos_resp.status_code != 200:
        logger.error(f"YouTube API: Videos API error: {videos_resp.text}")
        return []

    final_videos = []
    for item in videos_resp.json().get("items", []):
        snippet = item.get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", thumbnails.get("default", {})).get("url", "")

        final_videos.append({
            "video_id": item.get("id"),
            "video_title": snippet.get("title", "No Title"),
            "channelTitle": snippet.get("channelTitle", "Unknown Channel"),
            "thumbnail_url": thumbnail_url,
            "publishTime": snippet.get("publishTime", snippet.get("publishedAt", ""))
        })

        if len(final_videos) >= maxResults:
            break

    logger.info(f"YouTube API: Search returned {len(final_videos)} videos after filtering.")
    return final_videos


def fetch_top_comments(video_id, max_results=10, youtube_token=None):
    if not youtube_token:
        logger.error("YouTube API: Missing YouTube OAuth token")
        return []

    headers = {
        "Authorization": f"Bearer {youtube_token}",
        "Accept": "application/json"
    }

    url = f"https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max_results,
        "order": "relevance"
    }

    logger.info(f"YouTube API: Comments request: {url} with params={params}")
    resp = requests.get(url, headers=headers, params=params)
    logger.info(f"YouTube API: Comments response status: {resp.status_code}")
    
    if resp.status_code != 200:
        logger.error(f"YouTube API: Comments API error: {resp.text}")
        return []

    data = resp.json()
    comments = []
    
    # Check if response has items
    items = data.get("items", [])
    if not items:
        logger.warning(f"YouTube API: No comments found for video {video_id}")
        return []
    
    logger.info(f"YouTube API: Found {len(items)} comment threads for video {video_id}")
    
    for item in items:
        try:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            text = snippet.get("textOriginal", "").strip()
            if text:
                comments.append(text)
        except (KeyError, TypeError) as e:
            logger.warning(f"YouTube API: Failed to extract comment text: {e}")
            continue

    logger.info(f"YouTube API: Extracted {len(comments)} valid comments from {len(items)} threads for video {video_id}")
    
    if not comments:
        logger.warning(f"YouTube API: No valid comments extracted for video {video_id}")
    
    return comments
