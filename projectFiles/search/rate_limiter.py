"""
Rate limiter for API requests to avoid exceeding quotas.
"""
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Rate limiter to control API request frequency."""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding the rate limit."""
        now = time.time()
        
        # Remove old requests outside the time window
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def wait_if_needed(self) -> Optional[float]:
        """
        Wait if necessary to avoid exceeding rate limit.
        
        Returns:
            Time waited in seconds, or None if no wait was needed
        """
        if self.can_make_request():
            return None
        
        # Calculate how long to wait
        oldest_request = self.requests[0]
        wait_time = oldest_request + self.time_window - time.time()
        
        if wait_time > 0:
            time.sleep(wait_time)
            return wait_time
        
        return None
    
    def record_request(self):
        """Record that a request was made."""
        self.requests.append(time.time())
    
    def get_remaining_requests(self) -> int:
        """Get the number of remaining requests in the current window."""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self) -> Optional[float]:
        """Get the time when the rate limit will reset."""
        if not self.requests:
            return None
        
        return self.requests[0] + self.time_window
