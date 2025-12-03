from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    MISSED = "missed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    id: str
    description: str
    source_message_id: int
    source_message_text: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    
    requested_at: datetime
    assigned_to: Optional[str] = None
    
    response_message_id: Optional[int] = None
    response_message_text: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    context: Optional[str] = None
    missed_reason: Optional[str] = None
    completion_evidence: Optional[str] = None

