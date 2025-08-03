from fastapi import FastAPI, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Optional
import logging
from youtube_api import search_youtube_videos, fetch_top_comments
from llm_analyzer import analyze_video_comments
from db.supabase_client import insert_job_result
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://comment-ui-flax.vercel.app"],  # your UI domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/analyze-youtube")
def analyze_youtube(
    query: str = Query(...),
    maxResults: int = Query(5, ge=1, le=50),
    order: str = Query("relevance"),
    regionCode: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    job_id: str = Query(...),  # keep it str or UUID
    authorization: Optional[str] = Header(None)
):
    
    logger.info(f"######### Analyzer Called #########")
    
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    youtube_token = authorization.split(" ")[1]
    logger.info(f"✅ Received request to analyze: '{query}' with job_id: {job_id}")

    # Run background job using a thread
    def run_analysis():
        try:
            videos = search_youtube_videos(query, maxResults, order, regionCode, youtube_token)
            # logger.info(f"🔍 Found {len(videos)} videos.")

            for idx, video in enumerate(videos):
                # logger.info(f"▶️ Analyzing video {idx + 1}/{len(videos)}: {video['video_title']}")

                comments = fetch_top_comments(video['video_id'], 10, youtube_token)
                analysis = analyze_video_comments(video, comments)

                # Check if analysis was successful (has content in pros, cons, or next_hot_topic)
                has_content = (analysis.get('pros') or analysis.get('cons') or analysis.get('next_hot_topic'))
                
                if has_content:
                    try:
                        insert_job_result(job_id, video, analysis)
                        # logger.info(f"✅ Inserted result for video {video['video_id']}")
                    except Exception as db_exc:
                        logger.error(f"❌ Failed to insert result for {video['video_id']}: {db_exc}")
                else:
                    logger.warning(f"⚠️ Skipping database insert for video {video['video_id']} - no analysis content (reason: {analysis.get('reason', 'Unknown')})")

        except Exception as e:
            logger.exception(f"🚨 Analysis error: {e}")

    Thread(target=run_analysis).start()

    return {"status": "started", "job_id": job_id}
