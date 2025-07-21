import os
from dotenv import load_dotenv
import requests
import json
import logging
import re
from langdetect import detect

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct:free")

EMOJI_PATTERN = re.compile('[\ 0-\uFFFF]', flags=re.UNICODE)

def is_english(text):
    try:
        return detect(text) == 'en'
    except Exception:
        return False

def remove_emoji(text):
    # Remove all emoji and non-text symbols
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+', '', text)

def simple_text(text):
    # Remove emoji, strip, and collapse whitespace
    text = remove_emoji(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_video_comments(video, comments):
    # Sanitize comments: remove empty, whitespace-only, duplicate, non-English, emoji, keep only simple text, and ignore comments > 100 words
    seen = set()
    sanitized_comments = []
    for c in comments:
        c_clean = simple_text(c)
        if c_clean and c_clean not in seen and is_english(c_clean):
            if len(c_clean.split()) <= 100:
                sanitized_comments.append(c_clean)
                seen.add(c_clean)
    logger.info(f"Sanitized comments for video {video['video_id']} (count: {len(sanitized_comments)}): {sanitized_comments}")
    prompt = build_prompt(video, sanitized_comments)
    logger.info(f"LLM Prompt for video {video['video_id']}:\n{prompt}")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://openrouter.ai/",
        "X-Title": "YouTube Comment Analyzer"
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    logger.info(f"Sending request to OpenRouter LLM API for video {video['video_id']}...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    logger.info(f"OpenRouter LLM API response status: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"OpenRouter LLM API error: {response.text}")
        return {
            "video_id": video["video_id"],
            "video_title": video["video_title"],
            "channelTitle": video["channelTitle"],
            "thumbnail_url": video["thumbnail_url"],
            "publishTime": video["publishTime"],
            "pros": "",
            "cons": "",
            "next_hot_topic": ""
        }
    content = response.json()["choices"][0]["message"]["content"]
    logger.info(f"Raw LLM response content for video {video['video_id']}:\n{content}")
    try:
        result = json.loads(content[content.find('{'):content.rfind('}')+1])
    except Exception as e:
        logger.error(f"Error parsing LLM response for video {video['video_id']}: {e}")
        # Fallback: extract sections from plain text
        result = extract_sections_from_text(content)
    return {
        "video_id": video["video_id"],
        "video_title": video["video_title"],
        "channelTitle": video["channelTitle"],
        "thumbnail_url": video["thumbnail_url"],
        "publishTime": video["publishTime"],
        "pros": result.get("pros", ""),
        "cons": result.get("cons", ""),
        "next_hot_topic": result.get("next_hot_topic", "")
    }

def build_prompt(video, comments):
    comments_str = "\n- ".join(comments[:50])
    prompt = (
        f"You are a comment analyzer. Using the following comments, tell pros, cons, and next hot topic.\n\n"
        f"Video Title: {video['video_title']}\n"
        f"Channel: {video['channelTitle']}\n\n"
        f"comments:\n- {comments_str}\n\n"
        "Respond ONLY in valid JSON with these keys: pros, cons, next_hot_topic.\n"
        "Example:\n"
        "{\n"
        "  \"pros\": \"...\",\n"
        "  \"cons\": \"...\",\n"
        "  \"next_hot_topic\": \"...\"\n"
        "}\n\n"
        "pros:\ncons:\nnext_hot_topic:"
    )
    logger.info(f"Prompt built for video {video['video_id']} (first 300 chars): {prompt[:300]}")
    return prompt

def extract_sections_from_text(text):
    # Try to extract pros, cons, next_hot_topic from plain text using regex or section splitting
    pros = cons = next_hot_topic = ""
    # Use regex to find sections
    pros_match = re.search(r"pros\s*[:\-\n]+(.*?)(cons\s*[:\-\n]+|next hot topic\s*[:\-\n]+|$)", text, re.IGNORECASE | re.DOTALL)
    cons_match = re.search(r"cons\s*[:\-\n]+(.*?)(next hot topic\s*[:\-\n]+|pros\s*[:\-\n]+|$)", text, re.IGNORECASE | re.DOTALL)
    next_match = re.search(r"next hot topic\s*[:\-\n]+(.*?)(pros\s*[:\-\n]+|cons\s*[:\-\n]+|$)", text, re.IGNORECASE | re.DOTALL)
    if pros_match:
        pros = pros_match.group(1).strip().rstrip('1234567890.\n- ')
    if cons_match:
        cons = cons_match.group(1).strip().rstrip('1234567890.\n- ')
    if next_match:
        next_hot_topic = next_match.group(1).strip().rstrip('1234567890.\n- ')
    return {"pros": pros, "cons": cons, "next_hot_topic": next_hot_topic} 