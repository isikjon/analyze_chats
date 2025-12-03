from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class MessageRole(str, Enum):
    CLIENT = "client"
    DEVELOPER = "developer"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ChatMessage(BaseModel):
    id: int
    text: str
    role: MessageRole
    timestamp: datetime
    reply_to_message_id: Optional[int] = None
    reply_to_message: Optional['ChatMessage'] = None
    raw_data: Optional[dict] = None


class ChatSession(BaseModel):
    chat_id: str
    chat_title: Optional[str] = None
    source: str
    messages: List[ChatMessage] = Field(default_factory=list)
    total_messages: int = 0
    imported_at: datetime = Field(default_factory=datetime.now)

