import time
from collections import defaultdict
from fastapi import HTTPException, Request
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = settings.MAX_REQUESTS_PER_MINUTE
        self.window_size = 60  # 1 minute in seconds
    
    async def check_rate_limit(self, request: Request = None):
        """Check if the request is within rate limits"""
        # For simplicity, we'll use a global rate limit
        # In production, you'd want to use client IP or API key
        client_id = "global"
        
        current_time = time.time()
        
        # Clean old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.window_size
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per minute."
            )
        
        # Add current request
        self.requests[client_id].append(current_time)
        
        return True