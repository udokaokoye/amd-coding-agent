"""
Utility functions for the Task Manager.
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional


def generate_id(prefix: str = "id") -> str:
    """Generate a unique ID based on timestamp and random hash."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    hash_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"{prefix}_{hash_suffix}"


def parse_due_date(date_string: str) -> Optional[datetime]:
    """
    Parse a human-friendly date string into a datetime object.
    
    Supports formats:
    - "tomorrow"
    - "next week"
    - "in 3 days"
    - "2024-12-31"
    - "Dec 31, 2024"
    """
    date_string = date_string.lower().strip()
    now = datetime.now()
    
    if date_string == "tomorrow":
        return now + timedelta(days=1)
    
    if date_string == "next week":
        return now + timedelta(weeks=1)
    
    # "in X days/hours/weeks"
    match = re.match(r"in (\d+) (day|hour|week|month)s?", date_string)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == "hour":
            return now + timedelta(hours=amount)
        elif unit == "day":
            return now + timedelta(days=amount)
        elif unit == "week":
            return now + timedelta(weeks=amount)
        elif unit == "month":
            return now + timedelta(days=amount * 30)  # Approximate
    
    # ISO format: 2024-12-31
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        pass
    
    # Human format: Dec 31, 2024
    try:
        return datetime.strptime(date_string, "%b %d, %Y")
    except ValueError:
        pass
    
    return None


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to a maximum length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_relative_time(dt: datetime) -> str:
    """Format a datetime as a relative time string (e.g., '2 hours ago')."""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")


def validate_title(title: str) -> tuple[bool, str]:
    """
    Validate a task title.
    Returns (is_valid, error_message).
    """
    if not title or not title.strip():
        return False, "Title cannot be empty"
    
    if len(title) > 200:
        return False, "Title must be 200 characters or less"
    
    if len(title) < 3:
        return False, "Title must be at least 3 characters"
    
    return True, ""


def extract_tags(text: str) -> list[str]:
    """Extract hashtags from text (e.g., '#urgent #work')."""
    pattern = r'#(\w+)'
    matches = re.findall(pattern, text)
    return [tag.lower() for tag in matches]


class TaskStats:
    """Calculate statistics for a collection of tasks."""
    
    def __init__(self, tasks: list):
        self.tasks = tasks
    
    @property
    def total(self) -> int:
        return len(self.tasks)
    
    @property
    def completed(self) -> int:
        return sum(1 for t in self.tasks if t.status.value == "done")
    
    @property
    def completion_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100
    
    @property
    def overdue(self) -> int:
        now = datetime.now()
        return sum(
            1 for t in self.tasks 
            if t.due_date and t.due_date < now and t.status.value != "done"
        )
    
    def by_priority(self) -> dict[str, int]:
        counts = {}
        for task in self.tasks:
            priority = task.priority.value
            counts[priority] = counts.get(priority, 0) + 1
        return counts
    
    def by_status(self) -> dict[str, int]:
        counts = {}
        for task in self.tasks:
            status = task.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts
