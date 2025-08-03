from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "YOUR_SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_job_result(job_id: int, video: dict, analysis: dict):
    """
    Inserts a job result into the job_results table in Supabase.
    Maps summary to next_hot_topic from analysis.
    Args:
        job_id: BIGINT job ID (not UUID)
        video: Video data dictionary
        analysis: Analysis results dictionary
    Returns:
        APIResponse: The response object from supabase-py. Check .data for inserted rows.
    """
    data = {
        "job_id": job_id,  # Now BIGINT instead of UUID
        "video_id": video["video_id"],
        "channel_title": video.get("channelTitle"),
        "video_title": video.get("video_title"),
        "thumbnail_url": video.get("thumbnail_url"),
        "pros": analysis.get("pros"),
        "cons": analysis.get("cons"),
        "summary": analysis.get("next_hot_topic"),
    }
    
    # Log the data being inserted for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Database: Inserting job result: job_id={job_id}, video_id={video['video_id']}")
    logger.info(f"Database: Analysis data: pros='{analysis.get('pros', '')[:100]}...', cons='{analysis.get('cons', '')[:100]}...', next_hot_topic='{analysis.get('next_hot_topic', '')[:100]}...'")
    
    # Check if all analysis fields are empty
    if not analysis.get('pros') and not analysis.get('cons') and not analysis.get('next_hot_topic'):
        logger.warning(f"Database: All analysis fields are empty for video {video['video_id']}")
    
    try:
        # The returned object has a .data attribute with the inserted rows
        response = supabase.table("job_results").insert(data).execute()
        logger.info(f"Database: Successfully inserted job result for video {video['video_id']}")
        return response
    except Exception as e:
        logger.error(f"Database: Failed to insert job result for video {video['video_id']}: {e}")
        raise 