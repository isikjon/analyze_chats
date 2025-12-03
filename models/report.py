from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.task import Task
else:
    from models.task import Task


class ReportSummary(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    missed_tasks: int = 0
    in_progress_tasks: int = 0


class AnalysisReport(BaseModel):
    chat_id: str
    chat_title: Optional[str] = None
    analyzed_at: datetime = Field(default_factory=datetime.now)
    summary: ReportSummary
    tasks: List[Task] = Field(default_factory=list)
    missed_tasks: List[Task] = Field(default_factory=list)

