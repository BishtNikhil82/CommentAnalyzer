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

def ensure_str(val):
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return str(val) if val is not None else ""

openrouter_models = [
    "mistralai/mistral-7b-instruct",
    "openchat/openchat-3.5-0106",
    "huggingfaceh4/zephyr-7b-alpha",
    "meta-llama/llama-2-7b-chat",
    "google/gemma-7b-it",
    "nousresearch/nous-capybara-7b",
    "gryphe/mythomist-7b",
    "openrouter/cinematika-7b-v2"
]

def analyze_video_comments(video, comments):
    comments_fetched = len(comments)
    # Sanitize comments
    seen = set()
    sanitized_comments = []
    for c in comments:
        c_clean = simple_text(c)
        if c_clean and c_clean not in seen and is_english(c_clean):
            if len(c_clean.split()) <= 100:
                sanitized_comments.append(c_clean)
                seen.add(c_clean)
    comments_sanitized = len(sanitized_comments)
    
    logger.info(f"Video {video['video_id']}: {comments_fetched} comments fetched, {comments_sanitized} sanitized")
    
    base_response = {
        "video_id": video["video_id"],
        "video_title": video["video_title"],
        "channelTitle": video["channelTitle"],
        "thumbnail_url": video["thumbnail_url"],
        "publishTime": video["publishTime"],
        "pros": "",
        "cons": "",
        "next_hot_topic": "",
        "comments_fetched": comments_fetched,
        "comments_sanitized": comments_sanitized
    }

    if not sanitized_comments:
        base_response["reason"] = "No valid comments found after filtering." if comments_fetched > 0 else "No comments fetched from API."
        logger.warning(f"Video {video['video_id']}: {base_response['reason']}")
        return base_response

    prompt = build_prompt(video, sanitized_comments)
    #logger.info(f"LLM Prompt for video {video['video_id']}:\n{prompt}")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://openrouter.ai/",
        "X-Title": "YouTube Comment Analyzer"
    }
    
    last_error = None
    for model in openrouter_models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes YouTube comments."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                logger.info(f"Raw LLM response for video {video['video_id']} (model {model}):\n{content}")
                
                if not content or content.strip() == "":
                    logger.error(f"LLM API returned empty response for video {video['video_id']} (model {model})")
                    last_error = "Empty response from LLM API"
                    continue
                
                result = extract_sections_from_text(content)
                logger.info(f"Extracted sections for video {video['video_id']}: pros='{result.get('pros', '')[:100]}...', cons='{result.get('cons', '')[:100]}...', next_hot_topic='{result.get('next_hot_topic', '')[:100]}...'")
                
                # Check if all sections are empty
                if not result.get('pros') and not result.get('cons') and not result.get('next_hot_topic'):
                    logger.error(f"LLM API: All extracted sections are empty for video {video['video_id']} (model {model})")
                    last_error = "All extracted sections are empty"
                    continue
                
                base_response.update(result)
                return base_response
            elif response.status_code in [429, 403]:
                logger.warning(f"LLM API: Model {model} rate limited (status {response.status_code}), trying next model...")
                last_error = response.text
                continue
            else:
                logger.error(f"LLM API error (model {model}): {response.text}")
                last_error = response.text
                break
        except Exception as e:
            logger.error(f"LLM API: Exception calling model {model} for video {video['video_id']}: {e}")
            last_error = str(e)
            continue
    
    logger.error(f"LLM API: All models failed for video {video['video_id']}. Last error: {last_error}")
    base_response["reason"] = "LLM analysis failed for all models."
    return base_response

def build_prompt(video, comments):
    comments_str = "\n- ".join(comments[:50])
    prompt = (
        f"You are a YouTube comment analyzer. Analyze the following comments and provide insights.\n\n"
        f"Video Title: {video['video_title']}\n"
        f"Channel: {video['channelTitle']}\n"
        f"Comments:\n{comments_str}\n\n"
        "Analyze the comments and provide a response in this EXACT format:\n\n"
        "PROS:\n"
        "- List positive aspects mentioned by viewers\n"
        "- Focus on content quality, presentation, accuracy\n\n"
        "CONS:\n"
        "- List criticisms and areas for improvement\n"
        "- Focus on specific issues mentioned\n"
        "- Do NOT include topic suggestions or requests for future videos here.\n"
        "- If a viewer suggests a new topic, do NOT list it as a con.\n\n"
        "NEXT HOT TOPIC:\n"
        "- List 2-3 specific topics viewers want to see next\n"
        "- Base these on questions and interests in comments\n"
        "- Do NOT repeat cons. Only include new topic ideas here.\n\n"
        "Keep each section concise with clear bullet points. No explanations needed."
    )
    #logger.info(f"Prompt built for video {video['video_id']} (first 300 chars): {prompt[:300]}")
    return prompt

def extract_sections_from_text(text):
    logger.info(f"Extracting sections from text (first 200 chars): {text[:200]}...")
    
    # First try to parse as JSON if it looks like JSON
    if '{' in text and '}' in text:
        try:
            json_str = text[text.find('{'):text.rfind('}')+1]
            result = json.loads(json_str)
            pros = result.get("pros", [])
            cons = result.get("cons", [])
            next_hot_topic = result.get("next_hot_topic", [])
            if isinstance(pros, str):
                pros = [pros]
            if isinstance(cons, str):
                cons = [cons]
            if isinstance(next_hot_topic, str):
                next_hot_topic = [next_hot_topic]
            # Remove overlap between cons and next_hot_topic
            cons_clean = [c for c in cons if c.strip() and c.strip() not in next_hot_topic]
            next_clean = [n for n in next_hot_topic if n.strip()]
            result = {
                "pros": "\n".join([p.strip() for p in pros if p.strip()]),
                "cons": "\n".join(cons_clean),
                "next_hot_topic": "\n".join(next_clean)
            }
            logger.info(f"JSON parsing successful: pros={len(result['pros'])}, cons={len(result['cons'])}, next_hot_topic={len(result['next_hot_topic'])}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"LLM API: JSON parsing failed: {e}")
            pass

    # If JSON parsing fails, use regex to extract sections
    pros = cons = next_hot_topic = ""
    def extract_bullet_points(section_text):
        if not section_text:
            return []
        points = re.findall(r'(?:^|\n)[•\-\*]\s*([^\n]+)', section_text, re.MULTILINE)
        return [point.strip() for point in points] if points else [section_text.strip()]

    pros_match = re.search(r"(?:PROS:|POSITIVE)[:\s]*(.*?)(?=(?:CONS:|NEXT HOT TOPIC:|$))", text, re.IGNORECASE | re.DOTALL)
    cons_match = re.search(r"(?:CONS:|NEGATIVE)[:\s]*(.*?)(?=(?:PROS:|NEXT HOT TOPIC:|$))", text, re.IGNORECASE | re.DOTALL)
    next_match = re.search(r"(?:NEXT HOT TOPIC|SUGGESTED TOPIC)[:\s]*(.*?)(?=(?:PROS:|CONS:|$))", text, re.IGNORECASE | re.DOTALL)
    
    logger.info(f"Regex matches: pros={bool(pros_match)}, cons={bool(cons_match)}, next={bool(next_match)}")
    
    pros_list = extract_bullet_points(pros_match.group(1)) if pros_match else []
    cons_list = extract_bullet_points(cons_match.group(1)) if cons_match else []
    next_list = extract_bullet_points(next_match.group(1)) if next_match else []
    
    # Remove overlap between cons and next_hot_topic
    cons_clean = [c for c in cons_list if c and c not in next_list]
    next_clean = [n for n in next_list if n]
    
    result = {
        "pros": "\n".join([p for p in pros_list if p]),
        "cons": "\n".join(cons_clean),
        "next_hot_topic": "\n".join(next_clean)
    }
    
    logger.info(f"Regex extraction: pros={len(result['pros'])}, cons={len(result['cons'])}, next_hot_topic={len(result['next_hot_topic'])}")
    
    # Log if all sections are empty after regex extraction
    if not result['pros'] and not result['cons'] and not result['next_hot_topic']:
        logger.error(f"LLM API: All sections empty after regex extraction for text: {text[:200]}...")
    
    return result 