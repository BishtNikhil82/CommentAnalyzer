from db.supabase_client import insert_job_result
import uuid

def test_insert_job_result():
    job_id = "b7e6a1c2-3f4d-4e2a-9b1a-2c3d4e5f6a7b"
    video = {
        "video_id": "test_video_id",
        "channelTitle": "Test Channel",
        "video_title": "Test Video Title",
        "thumbnail_url": "https://example.com/thumbnail.jpg"
    }
    analysis = {
        "pros": "Good content, informative.",
        "cons": "Audio quality could be better.",
        "next_hot_topic": "Future of AI in Education"
    }
    response = insert_job_result(job_id, video, analysis)
    print("Insert response:", response)
    # The response should have a non-empty 'data' attribute if successful
    assert response.data is not None and len(response.data) > 0 