"""
Sample Project - Task Manager API
A simple REST-like task management system for demo purposes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import json


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data.get("priority", "medium")),
            status=Status(data.get("status", "todo")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            tags=data.get("tags", [])
        )


class TaskManager:
    """Manages a collection of tasks with CRUD operations."""
    
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._next_id = 1
    
    def create_task(self, title: str, **kwargs) -> Task:
        """Create a new task."""
        task_id = f"task_{self._next_id}"
        self._next_id += 1
        
        task = Task(id=task_id, title=title, **kwargs)
        self._tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Update a task's fields."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def list_tasks(
        self,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        tag: Optional[str] = None
    ) -> list[Task]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    def get_overdue_tasks(self) -> list[Task]:
        """Get all tasks past their due date."""
        now = datetime.now()
        return [
            t for t in self._tasks.values()
            if t.due_date and t.due_date < now and t.status != Status.DONE
        ]
    
    def export_to_json(self, filepath: str) -> None:
        """Export all tasks to a JSON file."""
        data = [t.to_dict() for t in self._tasks.values()]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filepath: str) -> int:
        """Import tasks from a JSON file. Returns count of imported tasks."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        count = 0
        for item in data:
            task = Task.from_dict(item)
            self._tasks[task.id] = task
            count += 1
        
        return count


# CLI Interface
def main():
    manager = TaskManager()
    
    # Create some sample tasks
    task1 = manager.create_task(
        "Build NPU demo",
        description="Create a coding agent demo for AMD collaboration",
        priority=Priority.HIGH,
        tags=["amd", "demo", "urgent"]
    )
    
    task2 = manager.create_task(
        "Record short-form content",
        description="Film and edit the TikTok/Reels video",
        priority=Priority.HIGH,
        tags=["content", "amd"]
    )
    
    task3 = manager.create_task(
        "Review final cut",
        priority=Priority.MEDIUM,
        tags=["content"]
    )
    
    # Update a task
    manager.update_task(task1.id, status=Status.IN_PROGRESS)
    
    # List all tasks
    print("📋 All Tasks:")
    print("-" * 40)
    for task in manager.list_tasks():
        status_icon = {
            Status.TODO: "⬜",
            Status.IN_PROGRESS: "🔄",
            Status.DONE: "✅",
            Status.ARCHIVED: "📦"
        }[task.status]
        print(f"{status_icon} [{task.priority.value.upper()}] {task.title}")
    
    print()
    print(f"Total tasks: {len(manager.list_tasks())}")
    print(f"In progress: {len(manager.list_tasks(status=Status.IN_PROGRESS))}")
    print(f"High priority: {len(manager.list_tasks(priority=Priority.HIGH))}")


if __name__ == "__main__":
    main()
