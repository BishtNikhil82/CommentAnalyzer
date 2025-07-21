import os
from dotenv import load_dotenv
import requests
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Returns a list of dicts: video_id, video_title, channelTitle, thumbnail_url, publishTime
def search_youtube_videos(query, maxResults=5, order="relevance", regionCode=None):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": maxResults,
        "order": order,
        "key": YOUTUBE_API_KEY
    }
    if regionCode:
        params["regionCode"] = regionCode
    logger.info(f"YouTube Search API request: {url} params={params}")
    resp = requests.get(url, params=params)
    logger.info(f"YouTube Search API response status: {resp.status_code}")
    if resp.status_code != 200:
        logger.error(f"YouTube API error: {resp.text}")
        return []
    data = resp.json()
    videos = []
    for item in data.get("items", []):
        snippet = item["snippet"]
        video_id = item["id"]["videoId"]
        video_title = snippet["title"]
        channelTitle = snippet["channelTitle"]
        thumbnail_url = snippet["thumbnails"].get("high", snippet["thumbnails"]["default"])['url']
        publishTime = snippet.get("publishTime", snippet.get("publishedAt", ""))
        videos.append({
            "video_id": video_id,
            "video_title": video_title,
            "channelTitle": channelTitle,
            "thumbnail_url": thumbnail_url,
            "publishTime": publishTime
        })
    logger.info(f"YouTube Search API returned {len(videos)} videos.")
    return videos

def fetch_top_comments(video_id, max_results=20):
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&order=relevance&key={YOUTUBE_API_KEY}"
    logger.info(f"YouTube Comments API request: {url}")
    resp = requests.get(url)
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
    logger.info(f"YouTube Comments API returned {len(comments)} comments for video {video_id}.")
    return comments 