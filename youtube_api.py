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

def search_youtube_videos(query, maxResults=1, order="relevance", regionCode=None, youtube_token=None):
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
        "order": order
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
        duration_seconds = _parse_duration(item.get("contentDetails", {}).get("duration"))
        if duration_seconds < 300:  # Skip videos less than 5 minutes
            continue

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

def fetch_top_comments(video_id, max_results=10, youtube_token=None):
    if not youtube_token:
        logger.error("Missing YouTube OAuth token")
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

    logger.info(f"YouTube Comments API request: {url} with params={params}")
    resp = requests.get(url, headers=headers, params=params)
    logger.info(f"YouTube Comments API response status: {resp.status_code}")
    if resp.status_code != 200:
        logger.error(f"YouTube Comments API error: {resp.text}")
        return []

    data = resp.json()
    comments = []
    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        text = snippet.get("textOriginal", "").strip()
        if text:
            comments.append(text)

    return comments
